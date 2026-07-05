use std::{
    process::{Child, Command, Stdio},
    sync::{Mutex, OnceLock},
};

static AGENT_SERVER: OnceLock<Mutex<Option<Child>>> = OnceLock::new();

#[tauri::command]
fn start_agent_server() -> Result<String, String> {
    let server = AGENT_SERVER.get_or_init(|| Mutex::new(None));
    let mut guard = server.lock().map_err(|_| "server lock poisoned".to_string())?;
    if guard.is_some() {
        return Ok("already-running".to_string());
    }

    let child = Command::new("uv")
        .args([
            "run",
            "uvicorn",
            "agent_server.app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|error| error.to_string())?;

    *guard = Some(child);
    Ok("started".to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let result = tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![start_agent_server])
        .run(tauri::generate_context!());

    if let Err(error) = result {
        eprintln!("error while running tauri application: {error}");
        std::process::exit(1);
    }
}
