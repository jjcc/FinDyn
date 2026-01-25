#!/usr/bin/env python3
"""
Stock Chart Visualization Wrapper

This script provides a convenient wrapper to visualize stock price data using any of the
available chart types: basic (matplotlib), advanced (mplfinance), or interactive (plotly).
"""

import argparse
import os
import sys
import subprocess

def main():
    parser = argparse.ArgumentParser(description='Generate stock charts with different visualization tools')
    parser.add_argument('file_path', help='Path to the CSV file containing stock data')
    parser.add_argument('--chart-type', '-t', choices=['basic', 'advanced', 'interactive'], 
                        default='interactive', help='Chart type to generate (default: interactive)')
    parser.add_argument('--output', '-o', help='Path to save the chart (optional)')
    
    args = parser.parse_args()
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set the script path based on chart type
    if args.chart_type == 'basic':
        script_path = os.path.join(script_dir, 'stock_chart.py')
    elif args.chart_type == 'advanced':
        script_path = os.path.join(script_dir, 'stock_chart_advanced.py')
    else:  # interactive
        script_path = os.path.join(script_dir, 'stock_chart_interactive.py')
    
    # Build the command
    cmd = [sys.executable, script_path, args.file_path]
    if args.output:
        cmd.extend(['--output', args.output])
    
    # Execute the selected script
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing {args.chart_type} chart: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Script '{script_path}' not found.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()