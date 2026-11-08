#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use eframe::egui;
use rfd::FileDialog;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use std::time::{Duration, Instant};

// =========================================================================
// GITHUB INTEGRATED REPOSITORY STORAGE CONFIGURATION
// Place your personal details and Access Token parameter strings here
// =========================================================================
const GITHUB_OWNER: &str = "ttmeticks-source";
const GITHUB_REPO: &str = "Premium-Apps";
const GITHUB_TOKEN: &str = "YOUR_GITHUB_PERSONAL_ACCESS_TOKEN_HERE";

#[derive(Serialize, Deserialize, Clone, Debug)]
struct UserEntry {
    username: String,
    password_plain: String,
    is_banned: bool,
    session_status: String, // "Offline", "Online", "KickPending"
}

#[derive(Serialize, Deserialize, Clone, Debug)]
struct ReportEntry {
    id: String,
    from_user: String,
    message: String,
    admin_reply: Option<String>,
    is_resolved: bool,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
struct NotificationEntry {
    username: String,
    message: String,
    is_read: bool,
}

fn main() -> Result<(), eframe::Error> {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([800.0, 650.0])
            .with_resizable(false),
        ..Default::default()
    };
    eframe::run_native(
        "Premium Apps Launcher",
        options,
        Box::new(|_cc| Box::new(PremiumAppsLauncher::new())),
    )
}

struct PremiumAppsLauncher {
    username_input: String,
    password_input: String,
    is_authenticated: bool,
    is_admin: bool,
    
    // Telemetry and background loop flags
    active_error_message: Option<String>,
    network_client: reqwest::blocking::Client,
    storage_dir: PathBuf,
    discovered_apps: Vec<String>,
    last_sync_time: Instant,
    
    // Core Data Registries
    cached_users: Vec<UserEntry>,
    cached_reports: Vec<ReportEntry>,
    cached_notifications: Vec<NotificationEntry>,
    
    // Admin View Workspace States
    search_user_query: String,
    selected_user: Option<UserEntry>,
    show_user_actions: bool,
    change_password_buffer: String,
    selected_report_id: Option<String>,
    admin_report_reply_buffer: String,
    
    // User View Workspace States
    support_ticket_buffer: String,
    active_ui_tab: String, // "Apps", "Support", "Notifications", "AdminUsers", "AdminReports"
    
    // Mid-screen Alert Notification Box variables
    timed_popup_message: Option<String>,
    timed_popup_end_time: Option<Instant>,
}

impl PremiumAppsLauncher {
    fn new() -> Self {
        let mut storage_dir = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
        storage_dir.push("PremiumApps_Storage");
        if !storage_dir.exists() {
            let _ = fs::create_dir_all(&storage_dir);
        }

        let mut app = Self {
            username_input: String::new(),
            password_input: String::new(),
            is_authenticated: false,
            is_admin: false,
            active_error_message: None,
            network_client: reqwest::blocking::Client::new(),
            storage_dir,
            discovered_apps: Vec::new(),
            last_sync_time: Instant::now(),
            cached_users: Vec::new(),
            cached_reports: Vec::new(),
            cached_notifications: Vec::new(),
            search_user_query: String::new(),
            selected_user: None,
            show_user_actions: false,
            change_password_buffer: String::new(),
            selected_report_id: None,
            admin_report_reply_buffer: String::new(),
            support_ticket_buffer: String::new(),
            active_ui_tab: "Apps".to_string(),
            timed_popup_message: None,
            timed_popup_end_time: None,
        };

        app.sync_all_github_files();
        app.check_auto_login();
        app.refresh_apps();
        app
    }

    fn check_auto_login(&mut self) {
        if let Some(home_path) = dirs::home_dir() {
            if let Some(user_dir_name) = home_path.file_name().and_then(|n| n.to_str()) {
                if user_dir_name == "ttmeticks" || user_dir_name == "ttmeticks-source" {
                    self.username_input = "PremiumOwner".to_string();
                    self.process_login_routine(true);
                }
            }
        }
    }

    fn refresh_apps(&mut self) {
        self.discovered_apps.clear();
        if let Ok(entries) = fs::read_dir(&self.storage_dir) {
            for entry in entries.flatten() {
                if let Ok(name) = entry.file_name().into_string() {
                    self.discovered_apps.push(name);
                }
            }
        }
    }

    // =========================================================================
    // NATIVE GITHUB INTEGRATED STORAGE DRIVER METHODS
    // =========================================================================

    fn fetch_github_file_content(&self, filename: &str) -> (String, String) {
        let url = format!("https://github.com{}/{}/contents/database/{}", GITHUB_OWNER, GITHUB_REPO, filename);
        let response = self.network_client.get(&url)
            .header("User-Agent", "PremiumLauncherApp")
            .header("Authorization", format!("token {}", GITHUB_TOKEN))
            .send();

        if let Ok(res) = response {
            if let Ok(json) = res.json::<serde_json::Value>() {
                if let Some(content_b64) = json["content"].as_str() {
                    let cleaned_b64 = content_b64.replace('\n', "").replace('\r', "");
                    if let Ok(decoded_bytes) = base64::decode(cleaned_b64) {
                        let text = String::from_utf8_lossy(&decoded_bytes).into_owned();
                        let sha = json["sha"].as_str().unwrap_or_default().to_string();
                        return (text, sha);
                    }
                }
            }
        }
        ("[]".to_string(), String::new())
    }

    fn write_github_file_content(&self, filename: &str, content: &str, sha: &str) {
        let url = format!("https://github.com{}/{}/contents/database/{}", GITHUB_OWNER, GITHUB_REPO, filename);
        let encoded_content = base64::encode(content);
        
        let mut body = serde_json::json!({
            "message": format!("Launcher Auto Sync: Update {}", filename),
            "content": encoded_content,
        });
        
        if !sha.is_empty() {
            body["sha"] = serde_json::json!(sha);
        }

        let _ = self.network_client.put(&url)
            .header("User-Agent", "PremiumLauncherApp")
            .header("Authorization", format!("token {}", GITHUB_TOKEN))
            .json(&body)
            .send();
    }

    fn sync_all_github_files(&mut self) {
        let (users_text, _) = self.fetch_github_file_content("users.json");
        if let Ok(users) = serde_json::from_str::<Vec<UserEntry>>(&users_text) {
            self.cached_users = users;
        }

        let (reports_text, _) = self.fetch_github_file_content("reports.json");
        if let Ok(reports) = serde_json::from_str::<Vec<ReportEntry>>(&reports_text) {
            self.cached_reports = reports;
        }

        let (notif_text, _) = self.fetch_github_file_content("notifications.json");
        if let Ok(notifs) = serde_json::from_str::<Vec<NotificationEntry>>(&notif_text) {
            self.cached_notifications = notifs;
        }
    }

    fn save_users_to_github(&self) {
        let text = serde_json::to_string_pretty(&self.cached_users).unwrap_or_default();
        let (_, sha) = self.fetch_github_file_content("users.json");
        self.write_github_file_content("users.json", &text, &sha);
    }

    fn save_reports_to_github(&self) {
        let text = serde_json::to_string_pretty(&self.cached_reports).unwrap_or_default();
        let (_, sha) = self.fetch_github_file_content("reports.json");
        self.write_github_file_content("reports.json", &text, &sha);
    }

    fn save_notifications_to_github(&self) {
        let text = serde_json::to_string_pretty(&self.cached_notifications).unwrap_or_default();
        let (_, sha) = self.fetch_github_file_content("notifications.json");
        self.write_github_file_content("notifications.json", &text, &sha);
    }

    // =========================================================================
    // LAUNCHER core WORKFLOW LOGIC
    // =========================================================================

    fn process_login_routine(&mut self, bypass: bool) {
        self.sync_all_github_files();
        let input_user = self.username_input.trim().to_string();
        let input_pass = self.password_input.trim();

        if let Some(user) = self.cached_users.iter().find(|u| u.username == input_user) {
            if user.is_banned {
                self.active_error_message = Some("Oops! This account has been banned by the administrator.".to_string());
                return;
            }
            if user.session_status == "Online" && !bypass {
                self.active_error_message = Some("Oops! Somebody has logged into Account. If U Cannot get the account back contact: sabi06119 On discord!".to_string());
                return;
            }
            if bypass || user.password_plain == input_pass {
                self.is_admin = (input_user == "PremiumOwner");
                self.is_authenticated = true;
                self.active_error_message = None;
                
                // Set online tracking lock state flags
                self.update_user_session_state(&input_user, "Online");
                self.check_and_trigger_unread_popup_alerts();
                return;
            }
        }
        
        if !bypass {
Use code with caution.
self.active_error_message = Some("Invalid account verification statement matches. Try again.".to_string());
}
}
fn update_user_session_state(&mut self, username: &str, state: &str) {
if let Some(user) = self.cached_users.iter_mut().find(|u| u.username == username) {
user.session_status = state.to_string();
self.save_users_to_github();
}
}
fn check_and_trigger_unread_popup_alerts(&mut self) {
let my_user = self.username_input.trim();
let mut alert_msg = None;
for notif in self.cached_notifications.iter_mut() {
if notif.username == my_user && !notif.is_read {
alert_msg = Some(notif.message.clone());
notif.is_read = true;
}
}
if let Some(msg) = alert_msg {
self.save_notifications_to_github();
self.timed_popup_message = Some(format!("🔔 Support Answered:\n{}", msg));
self.timed_popup_end_time = Some(Instant::now() + Duration::from_secs(3));
}
}
fn check_live_session_heartbeat_loop(&mut self) {
if !self.is_authenticated { return; }
if self.last_sync_time.elapsed() >= Duration::from_secs(4) {
self.sync_all_github_files();
self.last_sync_time = Instant::now();
let my_user = self.username_input.trim();
if let Some(user) = self.cached_users.iter().find(|u| u.username == my_user) {
if user.session_status == "KickPending" || user.is_banned {
self.is_authenticated = false;
self.active_error_message = Some("Oops! Somebody has logged into Account. If U Cannot get the account back contact: sabi06119 On discord!".to_string());
self.update_user_session_state(my_user, "Offline");
}
}
// Check for support notifications while the user is actively working inside the dashboard
self.check_and_trigger_unread_popup_alerts();
}
}
}
impl eframe::App for PremiumAppsLauncher {
fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
self.check_live_session_heartbeat_loop();
let mut visuals = egui::Visuals::dark();
visuals.window_fill = egui::Color32::from_rgb(0x12, 0x12, 0x12);
ctx.set_visuals(visuals);
// =========================================================================
// TIMED MID-SCREEN POPUP ALERT LAYOUT FRAME RENDERING
// =========================================================================
if let Some(end_time) = self.timed_popup_end_time {
if Instant::now() < end_time {
ctx.request_repaint(); // Keeps screen redrawing every frame to maintain the timer fluidly
egui::Window::new("System Notification Alert")
.anchor(egui::Align2::CENTER_CENTER, [0.0, 0.0])
.collapsible(false)
.resizable(false)
.title_bar(false)
.frame(egui::Frame::window(&visuals).fill(egui::Color32::from_rgb(0x1F, 0x1F, 0x1F)))
.show(ctx, |ui| {
ui.vertical_centered(|ui| {
ui.add_space(15.0);
if let Some(msg) = &self.timed_popup_message {
ui.label(egui::RichText::new(msg).color(egui::Color32::from_rgb(255, 215, 0)).size(16.0).strong());
}
ui.add_space(15.0);
});
});
return; // Freeze lower interactions while notification takes priority on screen
} else {
self.timed_popup_end_time = None;
self.timed_popup_message = None;
}
}
// =========================================================================
// PRIMARY APP RENDER VIEW STATES
// =========================================================================
if !self.is_authenticated {
egui::CentralPanel::default().show(ctx, |ui| {
ui.vertical_centered(|ui| {
ui.add_space(60.0);
ui.heading(egui::RichText::new("PREMIUM APPS").font(egui::FontId::proportional(32.0)).color(egui::Color32::from_rgb(255, 215, 0)).strong());
ui.add_space(20.0);
if let Some(err) = &self.active_error_message {
ui.group(|ui| {
ui.set_width(550.0);
ui.label(egui::RichText::new(err).color(egui::Color32::LIGHT_RED).strong().size(13.0));
});
ui.add_space(15.0);
}
egui::Grid::new("login_grid").spacing([10.0, 16.0]).show(ui, |ui| {
ui.label("Username:");
ui.add(egui::TextEdit::singleline(&mut self.username_input).desired_width(200.0));
ui.end_row();
ui.label("Password:");
ui.add(egui::TextEdit::singleline(&mut self.password_input).password(true).desired_width(200.0));
ui.end_row();
});
ui.add_space(30.0);
ui.horizontal(|ui| {
ui.add_space(250.0);
if ui.button(egui::RichText::new("Login Account").strong()).clicked() {
if !self.username_input.trim().is_empty() { self.process_login_routine(false); }
}
if ui.button("Create Account").clicked() {
if !self.username_input.trim().is_empty() && !self.password_input.trim().is_empty() {
let new_user = UserEntry {
username: self.username_input.trim().to_string(),
password_plain: self.password_input.trim().to_string(),
is_banned: false,
session_status: "Offline".to_string(),
};
self.cached_users.push(new_user);
self.save_users_to_github();
self.active_error_message = Some("Account successfully built! Click Login to enter Dashboard.".to_string());
}
}
});
});
});
} else {
// Main Top Navigation Panel Template Ribbon Strip
egui::TopBottomPanel::top("top_navigation_bar").fill(egui::Color32::from_rgb(0x1F, 0x1F, 0x1F)).show(ctx, |ui| {
ui.horizontal(|ui| {
ui.label(format!("User Profile: {} 🟢", self.username_input));
ui.separator();
if ui.selectable_label(self.active_ui_tab == "Apps", "📦 App Registry Frame").clicked() { self.active_ui_tab = "Apps".to_string(); }
if ui.selectable_label(self.active_ui_tab == "Support", "💬 Contact Support Hub").clicked() { self.active_ui_tab = "Support".to_string(); }
if ui.selectable_label(self.active_ui_tab == "Notifications", "🔔 View Alerts Tab").clicked() { self.active_ui_tab = "Notifications".to_string(); }
if self.is_admin {
ui.separator();
if ui.selectable_label(self.active_ui_tab == "AdminUsers", "⚙️ Manage Accounts").clicked() { self.active_ui_tab = "AdminUsers".to_string(); }
if ui.selectable_label(self.active_ui_tab == "AdminReports", "📋 Audit Open Tickets").clicked() { self.active_ui_tab = "AdminReports".to_string(); }
}
ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
if ui.button("Log Out").clicked() {
self.update_user_session_state(&self.username_input.clone(), "Offline");
self.is_authenticated = false;
self.username_input.clear();
self.password_input.clear();
}
});
});
});
egui::CentralPanel::default().show(ctx, |ui| {
match self.active_ui_tab.as_str() {
"Apps" => {
ui.heading(egui::RichText::new("APPLICATION ARCHIVE FRAME").color(egui::Color32::from_rgb(255, 215, 0)).strong());
ui.add_space(10.0);
if self.is_admin {
if ui.button("➕ Inject App File into Frame").clicked() {
if let Some(file) = FileDialog::new().pick_file() {
let dest = self.storage_dir.join(file.file_name().unwrap());
let _ = fs::copy(file, dest);
self.refresh_apps();
}
}
ui.add_space(10.0);
}
egui::ScrollArea::vertical().show(ui, |ui| {
for app_name in &self.discovered_apps {
ui.horizontal(|ui| {
ui.label(format!("📦 {}", app_name));
ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
if ui.button("Launch App").clicked() {
let target = self.storage_dir.join(app_name);
#[cfg(target_os = "windows")] { std::process::Command::new("cmd").args(["/C", target.to_str().unwrap()]).spawn(); }
#[cfg(target_os = "macos")] { std::process::Command::new("open").arg(target).spawn(); }
}
});
});
ui.separator();
}
});
},
"Support" => {
ui.heading(egui::RichText::new("CONTACT SUPPORT CENTER").color(egui::Color32::from_rgb(255, 215, 0)).strong());
ui.label("Describe your issue, report an item, or request assistance below:");
ui.add_space(10.0);
ui.add(egui::TextEdit::multiline(&mut self.support_ticket_buffer).hint_text("Type your message to PremiumOwner here...").desired_rows(6).desired_width(500.0));
ui.add_space(10.0);
if ui.button(egui::RichText::new("Submit Support Ticket File").strong()).clicked() {
if !self.support_ticket_buffer.trim().is_empty() {
let new_report = ReportEntry {
id: format!("{}", Instant::now().elapsed().as_millis()),
from_user: self.username_input.clone(),
message: self.support_ticket_buffer.trim().to_string(),
admin_reply: None,
is_resolved: false,
};
self.cached_reports.push(new_report);
self.save_reports_to_github();
self.support_ticket_buffer.clear();
}
}
},
"Notifications" => {
ui.heading(egui::RichText::new("NOTIFICATIONS ALERTS LIST").color(egui::Color32::from_rgb(255, 215, 0)).strong());
ui.add_space(10.0);
let my_user = self.username_input.trim();
egui::ScrollArea::vertical().show(ui, |ui| {
for notif in &self.cached_notifications {
if notif.username == my_user {
ui.group(|ui| {
ui.label(egui::RichText::new(&notif.message).color(egui::Color32::WHITE));
});
ui.add_space(5.0);
}
}
});
},
"AdminUsers" => {
ui.heading("👑 MANAGE USERS DASHBOARD FRAME");
ui.horizontal(|ui| {
ui.label("Filter Search User:");
ui.text_edit_singleline(&mut self.search_user_query);
});
ui.add_space(10.0);
if self.show_user_actions {
if let Some(user) = self.selected_user.clone() {
ui.group(|ui| {
ui.colored_label(egui::Color32::from_rgb(255, 215, 0), format!("Selected Action Target Profile: {}", user.username));
ui.horizontal(|ui| {
if ui.button("🚨 Terminate Account Session").clicked() {
if let Some(u) = self.cached_users.iter_mut().find(|x| x.username == user.username) {
u.session_status = "KickPending".to_string();
self.save_users_to_github();
}
self.show_user_actions = false;
}
let ban_lbl = if user.is_banned { "Remove Ban Tag" } else { "🚫 Issue Complete Ban" };
if ui.button(ban_lbl).clicked() {
if let Some(u) = self.cached_users.iter_mut().find(|x| x.username == user.username) {
u.is_banned = !u.is_banned;
u.session_status = "Offline".to_string();
self.save_users_to_github();
}
self.show_user_actions = false;
}
});
ui.horizontal(|ui| {
ui.label("Update Password:");
ui.text_edit_singleline(&mut self.change_password_buffer);
if ui.button("Save").clicked() {
if !self.change_password_buffer.trim().is_empty() {
if let Some(u) = self.cached_users.iter_mut().find(|x| x.username == user.username) {
u.password_plain = self.change_password_buffer.trim().to_string();
self.save_users_to_github();
}
self.change_password_buffer.clear();
self.show_user_actions = false;
}
}
if ui.button("Close Options").clicked() { self.show_user_actions = false; }
});
});
ui.add_space(10.0);
}
}
egui::Grid::new("admin_table").striped(true).spacing([20.0, 8.0]).show(ui, |ui| {
ui.label("User Handle");
ui.label("Password Text");
ui.label("Live Status");
ui.label("Action Menu");
ui.end_row();
for user in self.cached_users.clone() {
if !self.search_user_query.trim().is_empty() && !user.username.contains(self.search_user_query.trim()) {
continue;
}
ui.label(&user.username);
ui.label(&user.password_plain);
let state_lbl = if user.is_banned { "⛔ Banned" } else if user.session_status == "Online" { "🟢 Online" } else { "⚪ Offline" };
ui.label(state_lbl);
if ui.button(" • • • ").clicked() {
self.selected_user = Some(user);
self.show_user_actions = true;
}
ui.end_row();
}
});
},
"AdminReports" => {
ui.heading("📋 SUPPORT TICKETS AUDIT LOGS");
ui.add_space(10.0);
if let Some(rep_id) = &self.selected_report_id {
ui.group(|ui| {
ui.label(format!("Replying to Ticket Reference: {}", rep_id));
ui.add(egui::TextEdit::multiline(&mut self.admin_report_reply_buffer).desired_rows(3).desired_width(400.0));
ui.horizontal(|ui| {
if ui.button("Send Reply & Notification Alert").clicked() {
if let Some(report) = self.cached_reports.iter_mut().find(|r| &r.id == rep_id) {
report.admin_reply = Some(self.admin_report_reply_buffer.clone());
report.is_resolved = true;
// Append a tracking notification file block for the receiver user
self.cached_notifications.push(NotificationEntry {
username: report.from_user.clone(),
message: self.admin_report_reply_buffer.clone(),
is_read: false,
});
self.save_reports_to_github();
self.save_notifications_to_github();
self.admin_report_reply_buffer.clear();
self.selected_report_id = None;
}
}
if ui.button("Dismiss").clicked() { self.selected_report_id = None; }
});
});
ui.add_space(10.0);
}
egui::ScrollArea::vertical().show(ui, |ui| {
for r in &self.cached_reports {
ui.group(|ui| {
ui.horizontal(|ui| {
ui.label(egui::RichText::new(format!("From: {}", r.from_user)).strong());
ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
let status = if r.is_resolved { "🟢 Resolved" } else { "🔴 Open" };
ui.label(status);
if !r.is_resolved && ui.small_button("Reply Ticket").clicked() {
self.selected_report_id = Some(r.id.clone());
}
});
});
ui.label(format!("Message: {}", r.message));
if let Some(reply) = &r.admin_reply {
ui.colored_label(egui::Color32::LIGHT_GREEN, format!("Admin Answer: {}", reply));
}
});
ui.add_space(5.0);
}
});
},
_ => {}
}
});
}
}
}
