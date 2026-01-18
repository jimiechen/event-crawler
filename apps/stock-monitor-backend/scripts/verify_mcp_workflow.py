import requests
import json
import os
import time

BASE_URL = "http://localhost:8000/mcp"
DOC_TYPE = "technical_review"
TITLE = "MCP Workflow Verification"
INITIAL_CONTENT = "This is the initial content of the technical review."
AUTHOR = "Trae_Agent_Test"

def test_workflow():
    print("=== Starting MCP Workflow Verification ===")
    
    # 1. Create Document
    print("\n[Step 1] Creating Document...")
    create_payload = {
        "doc_type": DOC_TYPE,
        "title": TITLE,
        "content": INITIAL_CONTENT,
        "author": AUTHOR
    }
    try:
        response = requests.post(f"{BASE_URL}/collaboration/doc/create", json=create_payload)
        response.raise_for_status()
        result = response.json()
        print(f"Create Result: {json.dumps(result, indent=2)}")
        
        if not result.get("success"):
            print("Failed to create document.")
            return
            
        doc_path = result["filepath"]
        rel_path = result["filename"] # Note: API returns filename as rel_path sometimes, let's check
        # Actually API returns 'filepath' as full path and 'filename' as name.
        # But we need the relative path for update: "technical_review/filename.md"
        update_doc_path = f"{DOC_TYPE}/{result['filename']}"
        
        # Verify file exists
        if os.path.exists(doc_path):
            print(f"File verified at: {doc_path}")
        else:
            print(f"File NOT found at: {doc_path}")
            return

    except Exception as e:
        print(f"Error creating doc: {e}")
        return

    # 2. Update Document
    print("\n[Step 2] Updating Document...")
    time.sleep(1) # Ensure timestamp diff
    updated_content = "This is the UPDATED content.\n\n## Subsection\nSome details."
    signature = "Updated content with subsection."
    
    update_payload = {
        "doc_path": update_doc_path,
        "content": updated_content,
        "signature": signature,
        "author": AUTHOR
    }
    
    try:
        response = requests.post(f"{BASE_URL}/collaboration/doc/update", json=update_payload)
        response.raise_for_status()
        result = response.json()
        print(f"Update Result: {json.dumps(result, indent=2)}")
        
        if not result.get("success"):
            print("Failed to update document.")
            return

    except Exception as e:
        print(f"Error updating doc: {e}")
        return

    # 3. Verify Content
    print("\n[Step 3] Verifying Final Content...")
    try:
        with open(doc_path, 'r') as f:
            final_content = f.read()
        
        print("-" * 40)
        print(final_content)
        print("-" * 40)
        
        # Check Metadata
        if "- 文档版本: v1.0.1" in final_content:
            print("PASS: Version updated to v1.0.1")
        else:
            print("FAIL: Version not updated")
            
        if f"- 当前模型: {AUTHOR}" in final_content:
            print("PASS: Current model updated")
            
        if updated_content in final_content:
            print("PASS: Content updated")
            
        if signature in final_content:
            print("PASS: Signature added to log")
            
    except Exception as e:
        print(f"Error verifying content: {e}")

if __name__ == "__main__":
    test_workflow()
