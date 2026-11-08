#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use eframe::egui;
use rfd::FileDialog;
use sha2::{Digest, Sha256};
use std::fs;
use std::path::PathBuf;
use std::process::Command;

fn main() -> Result<(), eframe::Error> {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([600.0, 500.0])
            .with_resizable(false),
        ..Default::default()
    };
    eframe::run_native(
        "Premium Apps",
        options,
        Box::new(|_cc| Box::new(PremiumAppsLauncher::new())),
    )
}

struct PremiumAppsLauncher {
    username: String,
    password: String,
    is_authenticated: bool,
    is_admin: bool,
    storage_dir: PathBuf,
    discovered_apps: Vec<String>,
}

impl PremiumAppsLauncher {
    fn new() -> Self {
        let mut storage_dir = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
        storage_dir.push("PremiumApps_Storage");
        if !storage_dir.exists() {
            let _ = fs::create_dir_all(&storage_dir);
        }

        let mut app = Self {
            username: String::new(),
            password: String::new(),
            is_authenticated: false,
            is_admin: false,
            storage_dir,
            discovered_apps: Vec::new(),
        };
        app.refresh_apps();
        app
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

    fn check_credentials(&mut self) {
        // SHA-256 Hash of the administrative username to keep it hidden in binary code
        // Plaintext value target: "PremiumOwner"
        let admin_username_hash = "7726a27e74033320f78a7f43ec86c47cbff76ff8e4695b7331908ef9ff51b5c4";
        
        let mut hasher = Sha256::new();
        hasher.update(self.username.trim().as_bytes());
        let hashed_input = format!("{:x}", hasher.finalize());

        if hashed_input == admin_username_hash {
            self.is_admin = true;
        } else {
            self.is_admin = false;
        }
        self.is_authenticated = true;
    }
}

impl eframe::App for PremiumAppsLauncher {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // Set styling theme colors
        let mut visuals = egui::Visuals::dark();
        visuals.widgets.inactive.weak_bg_fill = egui::Color32::from_rgb(0x1F, 0x1F, 0x1F);
        visuals.window_fill = egui::Color32::from_rgb(0x12, 0x12, 0x12);
        ctx.set_visuals(visuals);

        if !self.is_authenticated {
            // Login view layout screen
            egui::CentralPanel::default().show(ctx, |ui| {
                ui.vertical_centered(|ui| {
                    ui.add_space(40.0);
                    ui.heading(egui::RichText::new("PREMIUM APPS").font(egui::FontId::proportional(28.0)).color(egui::Color32::from_rgb(255, 215, 0)).strong());
                    ui.add_space(40.0);

                    egui::Grid::new("login_form").spacing([10.0, 15.0]).show(ui, |ui| {
                        ui.label(egui::RichText::new("Username:").size(14.0).color(egui::Color32::WHITE));
                        ui.add(egui::TextEdit::singleline(&mut self.username).desired_width(200.0));
                        ui.end_row();

                        ui.label(egui::RichText::new("Password:").size(14.0).color(egui::Color32::WHITE));
                        ui.add(egui::TextEdit::singleline(&mut self.password).password(true).desired_width(200.0));
                        ui.end_row();
                    });

                    ui.add_space(30.0);
                    if ui.add(egui::Button::new(egui::RichText::new("Launch Dashboard").size(14.0).strong()).min_size(egui::vec2(180.0, 35.0))).clicked() {
                        if !self.username.trim().is_empty() && !self.password.trim().is_empty() {
                            self.check_credentials();
                        }
                    }
                });
            });
        } else {
            // Logged in framework panel dashboard view
            egui::TopBottomPanel::top("top_status").fill(egui::Color32::from_rgb(0x1F, 0x1F, 0x1F)).show(ctx, |ui| {
                ui.horizontal(|ui| {
                    let status_text = format!("Active User Session  |  Key: {}", self.password);
                    ui.label(egui::RichText::new(status_text).color(egui::Color32::LIGHT_GRAY).size(12.0));
                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        if ui.button("Exit Session").clicked() {
                            self.is_authenticated = false;
                            self.username.clear();
                            self.password.clear();
                        }
                    });
                });
            });

            egui::CentralPanel::default().show(ctx, |ui| {
                let panel_title = if self.is_admin { "ADMIN DEPLOYMENT PANEL" } else { "APPS REPOSITORY" };
                ui.heading(egui::RichText::new(panel_title).color(egui::Color32::from_rgb(255, 215, 0)).size(18.0).strong());
                ui.add_space(10.0);

                ui.group(|ui| {
                    ui.set_min_size(egui::vec2(560.0, 300.0));
                    ui.vertical(|ui| {
                        ui.label(egui::RichText::new("APPS FRAME").strong().color(egui::Color32::WHITE));
                        ui.separator();

                        if self.is_admin {
                            ui.horizontal(|ui| {
                                if ui.button("➕ Paste / Import App File").clicked() {
                                    if let Some(file) = FileDialog::new().pick_file() {
                                        let dest = self.storage_dir.join(file.file_name().unwrap());
                                        let _ = fs::copy(file, dest);
                                        self.refresh_apps();
                                    }
                                }
                                ui.label(egui::RichText::new("(Select any app file from your MacBook/PC to add it to the launcher)").italic().color(egui::Color32::GRAY));
                            });
                            ui.add_space(5.0);
                        }

                        egui::ScrollArea::vertical().show(ui, |ui| {
                            let mut app_to_run = None;
                            for app_name in &self.discovered_apps {
                                ui.horizontal(|ui| {
                                    ui.label(egui::RichText::new(format!("📦 {}", app_name)).color(egui::Color32::WHITE));
                                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                                        if ui.button("Download & Run").clicked() {
                                            app_to_run = Some(self.storage_dir.join(app_name));
                                        }
                                    });
                                });
                                ui.separator();
                            }

                            if let Some(path) = app_to_run {
                                #[cfg(target_os = "windows")]
                                {
                                    let _ = Command::new("cmd").args(["/C", path.to_str().unwrap()]).spawn();
                                }
                                #[cfg(target_os = "macos")]
                                {
                                    let _ = Command::new("open").arg(path).spawn();
                                }
                            }
                        });
                    });
                });
            });
        }
    }
}
