import sys
import os
import logging

# Add the current directory to sys.path so we can import scripts
sys.path.append(os.getcwd())

from scripts.parse_okooo_mobile import OkoooParser

logging.basicConfig(level=logging.INFO)

def test_parser():
    # Adjust these paths to be absolute or correct relative paths
    data_dir = "/Users/mac/StudioProjects/2026/open-citycloud-workspace/data/okooo/mobile_samples"
    output_dir = "/Users/mac/StudioProjects/2026/open-citycloud-workspace/data/okooo/processed_samples"
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    print(f"Processing data from {data_dir} to {output_dir}")
    parser = OkoooParser(data_dir, output_dir)
    parser.process_all()
    
    print("Parsing completed.")

if __name__ == "__main__":
    test_parser()
