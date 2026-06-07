use zed_extension_api::{self as zed, LanguageServerId, Result, Worktree};
use std::env;
use std::fs;

struct SkriptExtension;

impl zed::Extension for SkriptExtension {
    fn new() -> Self {
        Self
    }

    fn language_server_command(
        &mut self,
        _language_server_id: &LanguageServerId,
        worktree: &Worktree,
    ) -> Result<zed::Command> {
        let path = worktree
            .which("python")
            .or_else(|| worktree.which("python3"))
            .ok_or_else(|| "Python not found in PATH. Please install Python to use the Skript LSP.".to_string())?;

        // 1. Get current extension root
        let root = env::current_dir()
            .map_err(|e| format!("Failed to get current directory: {}", e))?;
        
        let script_path = root.join("skript_lsp.py");
        let api_json_path = root.join("docs").join("api.json");

        // 2. Deployment: Write the LSP script if missing in the work directory
        if !script_path.exists() {
             let lsp_code = include_str!("../skript_lsp.py");
             fs::write(&script_path, lsp_code).map_err(|e| format!("Failed to deploy LSP script: {}", e))?;
        }
        
        // 3. Deployment: Ensure docs folder and api.json exist
        let docs_dir = root.join("docs");
        if !docs_dir.exists() {
            fs::create_dir_all(&docs_dir).map_err(|e| format!("Failed to create docs dir: {}", e))?;
        }
        if !api_json_path.exists() {
            let api_json = include_str!("../docs/api.json");
            fs::write(&api_json_path, api_json).map_err(|e| format!("Failed to deploy API data: {}", e))?;
        }

        Ok(zed::Command {
            command: path,
            args: vec![script_path.to_string_lossy().to_string()],
            env: Default::default(),
        })
    }
}

zed::register_extension!(SkriptExtension);
