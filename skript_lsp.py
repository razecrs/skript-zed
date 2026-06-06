import sys
import json
import re
import os

# Load docs for Hover
DOCS = {}
try:
    with open(os.path.join(os.path.dirname(__file__), "docs/api.json"), 'r') as f:
        DOCS = json.load(f)
except:
    pass

def log(msg):
    with open("lsp.log", "a") as f:
        f.write(f"{msg}\n")

def send_response(response):
    content = json.dumps(response)
    sys.stdout.write(f"Content-Length: {len(content)}\r\n\r\n{content}")
    sys.stdout.flush()

# Keep track of open document text
DOCUMENTS = {}

def handle_request(request):
    method = request.get("method")
    params = request.get("params")
    
    if method == "initialize":
        send_response({
            "id": request["id"],
            "result": {
                "capabilities": {
                    "textDocumentSync": 1,
                    "completionProvider": {"triggerCharacters": [" ", ":"]},
                    "hoverProvider": True,
                    "documentSymbolProvider": True,
                    "documentFormattingProvider": True,
                    "renameProvider": True
                }
            }
        })
    
    elif method == "textDocument/rename":
        uri = params["textDocument"]["uri"]
        new_name = params["newName"]
        # In a single-file script, we rename every occurrence of the variable
        # For simplicity, we assume the user is renaming a variable in braces
        text = DOCUMENTS.get(uri, "")
        # Return workspace edits
        send_response({
            "id": request["id"],
            "result": {
                "changes": {
                    uri: [{
                        "range": {"start": {"line": 0, "character": 0}, "end": {"line": len(text.splitlines()), "character": 0}},
                        "newText": text.replace(params.get("oldName", ""), new_name) # Basic placeholder
                    }]
                }
            }
        })

    elif method == "textDocument/formatting":
        uri = params["textDocument"]["uri"]
        text = DOCUMENTS.get(uri, "")
        if not text:
            send_response({"id": request["id"], "result": []})
            return

        def var_fixer(match):
            return "{" + match.group(1).lower().replace(" ", "_") + "}"

        formatted_lines = []
        lines = text.splitlines()
        
        for line in lines:
            stripped = line.lstrip()
            indent_str = line[:len(line)-len(stripped)]
            
            if not stripped:
                formatted_lines.append("")
                continue
            
            # --- Cleanup 1: Comments ---
            if stripped.startswith("#"):
                comment_content = stripped[1:].strip()
                if comment_content:
                    stripped = f"# {comment_content}"
                else:
                    stripped = "#"
            else:
                # --- Cleanup 2: Variables ---
                # Standardization: {My Variable} -> {my_variable}
                stripped = re.sub(r"\{(.+?)\}", var_fixer, stripped)
                
                # --- Cleanup 3: Declarations (Colons) ---
                if any(stripped.startswith(x) for x in ["on ", "command ", "function ", "options", "test "]):
                    if not stripped.endswith(":"):
                        stripped = stripped + ":"
            
            formatted_lines.append(indent_str + stripped)

        new_text = "\n".join(formatted_lines)
        send_response({
            "id": request["id"],
            "result": [{
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": len(lines), "character": 0}
                },
                "newText": new_text
            }]
        })
    
    elif method == "textDocument/didOpen":
        uri = params["textDocument"]["uri"]
        text = params["textDocument"]["text"]
        DOCUMENTS[uri] = text
        send_diagnostics(uri, text)

    elif method == "textDocument/didChange":
        uri = params["textDocument"]["uri"]
        text = params["contentChanges"][0]["text"]
        DOCUMENTS[uri] = text
        send_diagnostics(uri, text)

    elif method == "textDocument/documentSymbol":
        uri = params["textDocument"]["uri"]
        text = DOCUMENTS.get(uri, "")
        symbols = []
        lines = text.splitlines()
        
        for i, line in enumerate(lines):
            clean = line.strip()
            # Capture Commands, Events, Functions
            # Symbol Kinds: 12 (Function), 6 (Method), 26 (Event)
            if clean.startswith("command /"):
                name = clean.split(":")[0]
                symbols.append(create_symbol(name, 12, i, 0, len(line)))
            elif clean.startswith("on "):
                name = clean.split(":")[0]
                symbols.append(create_symbol(name, 23, i, 0, len(line))) # Event
            elif clean.startswith("function "):
                name = clean.split(":")[0]
                symbols.append(create_symbol(name, 12, i, 0, len(line)))
            elif clean.startswith("test "):
                name = clean.split(":")[0]
                symbols.append(create_symbol(name, 13, i, 0, len(line))) # Variable/Constant proxy for Test
                
        send_response({"id": request["id"], "result": symbols})

    elif method == "textDocument/hover":
        # Provide local docs on hover
        send_response({"id": request["id"], "result": None})

    elif method == "textDocument/completion":
        completions = []
        for name, data in DOCS.items():
            completions.append({
                "label": data['name'],
                "kind": 3, # Function
                "detail": data['description'],
                "documentation": {"kind": "markdown", "value": data['examples']}
            })
        send_response({"id": request["id"], "result": completions})

def create_symbol(name, kind, line, start, end):
    return {
        "name": name,
        "kind": kind,
        "location": {
            "uri": "", # Filled by LSP protocol logic usually
            "range": {
                "start": {"line": line, "character": start},
                "end": {"line": line, "character": end}
            }
        }
    }

def send_diagnostics(uri, text):
    diagnostics = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        clean = line.strip()
        if not clean or clean.startswith("#"): continue
        if any(clean.startswith(x) for x in ["on ", "command ", "function ", "options:"]):
            if not clean.endswith(":"):
                diagnostics.append({
                    "range": {"start": {"line": i, "character": 0}, "end": {"line": i, "character": len(line)}},
                    "severity": 1,
                    "message": "Syntax Error: Declarations must end with a colon (:)"
                })
    
    send_response({
        "method": "textDocument/publishDiagnostics",
        "params": {"uri": uri, "diagnostics": diagnostics}
    })

def main():
    while True:
        line = sys.stdin.readline()
        if not line: break
        if line.startswith("Content-Length:"):
            length = int(line.split(":")[1].strip())
            sys.stdin.readline()
            content = sys.stdin.read(length)
            request = json.loads(content)
            handle_request(request)

if __name__ == "__main__":
    main()
