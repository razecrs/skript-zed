use zed_extension_api::{self as zed, LanguageServerId, Result, Worktree};
use std::env;

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

        // In a Zed extension, env::current_dir() returns the extension's root directory.
        let script_path = env::current_dir()
            .map(|path| path.join("skript_lsp.py").to_string_lossy().to_string())
            .unwrap_or_else(|_| "skript_lsp.py".to_string());

        Ok(zed::Command {
            command: path,
            args: vec![script_path],
            env: Default::default(),
        })
    }
}

zed::register_extension!(SkriptExtension);
