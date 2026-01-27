import os
import sys
from scripts.parse_okooo_mobile import OkoooParser

# Add the directory containing scripts to path so we can import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_update():
    # Use absolute paths
    base_dir = "/Users/mac/StudioProjects/2026/open-citycloud-workspace"
    data_dir = os.path.join(base_dir, "data/okooo/mobile_samples")
    output_dir = os.path.join(base_dir, "data/okooo/processed_samples")
    
    print(f"Testing parser with data from {data_dir}")
    print(f"Outputting to {output_dir}")
    
    if not os.path.exists(data_dir):
        print(f"Error: Data directory {data_dir} does not exist.")
        return

    parser = OkoooParser(data_dir, output_dir)
    success, fail = parser.process_all()
    
    print(f"Processed: Success={success}, Fail={fail}")
    
    # Verification
    match_id = "1314249"
    json_path = os.path.join(output_dir, f"{match_id}.json")
    
    if os.path.exists(json_path):
        print(f"Output file {json_path} created.")
        import json
        with open(json_path, 'r') as f:
            data = json.load(f)
            
            # Check Match Info (Date, Rank)
            info = data.get("match_info", {})
            print(f"Match Date: {info.get('score_text')}") # Usually contains date
            print(f"Home Rank: {info.get('home_rank')}")
            print(f"Away Rank: {info.get('away_rank')}")
            
            # Check Future Matches
            future = data.get("future_matches", {})
            print(f"Future Home: {len(future.get('home', []))} matches")
            print(f"Future Away: {len(future.get('away', []))} matches")
            
    else:
        print(f"Error: Output file {json_path} not found.")

    # Check Odds Change File
    # pid=82
    odds_dir = os.path.join(data_dir, "odds", "82")
    odds_file = os.path.join(odds_dir, f"{match_id}.json")
    
    if os.path.exists(odds_file):
        print(f"Odds change file {odds_file} created.")
        with open(odds_file, 'r') as f:
            changes = json.load(f)
            print(f"Odds changes count: {len(changes)}")
            if len(changes) > 0:
                print(f"Sample change: {changes[0]}")
    else:
        print(f"Odds change file {odds_file} NOT found.")
        # Note: In parse_okooo_mobile.py I used self.data_dir/odds/pid. 
        # Here data_dir is mobile_samples. So it should be mobile_samples/odds/82.
        # Let's check if the directory was created.

if __name__ == "__main__":
    test_update()
