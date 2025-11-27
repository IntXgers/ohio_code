# download_caselaw_recursive.py
import requests
from bs4 import BeautifulSoup
import zipfile
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time


class CaseLawDownloader:
    def __init__(self, base_url: str = "https://static.case.law",
                 output_dir: str = "../../../../ohio_caselaw"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def discover_ohio_reporters(self) -> list[str]:
        """
        Step 1: Scrape main page to find ALL Ohio reporter directories
        """
        print(f"🔍 Discovering Ohio reporters from {self.base_url}")

        response = requests.get(self.base_url)
        response.raise_for_status()

        # DEBUG: Save the HTML to see what we got
        with open('debug_page.html', 'w') as f:
            f.write(response.text)
        print("📝 Saved HTML to debug_page.html")

        soup = BeautifulSoup(response.text, 'html.parser')

        # DEBUG: Print first 10 links
        print("\n🔍 First 10 links found:")
        for i, link in enumerate(soup.find_all('a')[:10]):
            href = link.get('href')
            text = link.get_text()
            print(f"  {i + 1}. href='{href}' text='{text}'")

        ohio_reporters = []
        for link in soup.find_all('a'):
            href = link.get('href')
            text = link.get_text().strip()

            # Try both href and text content
            if href and 'ohio' in href.lower():
                reporter = href.strip().rstrip('/')
                if '/' in reporter:
                    reporter = reporter.split('/')[-1]
                if reporter.startswith('ohio'):
                    ohio_reporters.append(reporter)
            elif 'ohio' in text.lower() and text.startswith('ohio'):
                # Sometimes the link text IS the reporter name
                ohio_reporters.append(text)

        # Remove duplicates and sort
        ohio_reporters = sorted(set(ohio_reporters))

        print(f"\n✅ Found {len(ohio_reporters)} Ohio reporters:")
        for reporter in ohio_reporters:
            print(f"   - {reporter}")

        return ohio_reporters

    def get_zip_files(self, reporter_name: str) -> list[str]:
        """
        Step 2: For each reporter directory, find all .zip files
        """
        url = f"{self.base_url}/{reporter_name}/"
        print(f"\n🔍 Scanning {reporter_name} for zip files...")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except Exception as e:
            print(f"❌ Error accessing {url}: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all <a> tags with href ending in .zip
        zip_files = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.endswith('.zip'):
                # Extract just the filename (e.g., "4.zip")
                filename = href.split('/')[-1]
                zip_files.append(filename)

        # Sort numerically (1.zip, 2.zip, ..., 10.zip, 11.zip)
        try:
            zip_files.sort(key=lambda x: int(x.replace('.zip', '')))
        except:
            zip_files.sort()  # Fallback to alphabetical

        print(f"✅ Found {len(zip_files)} zip files in {reporter_name}")
        return zip_files

    def download_file(self, url: str, destination: Path) -> bool:
        """
        Step 3: Download a single zip file with progress
        Resume capability - skips if already exists
        """
        # Check if already downloaded (no hashing needed)
        if destination.exists():
            file_size = destination.stat().st_size
            if file_size > 0:  # Make sure it's not a partial download
                print(f"⏭️  Already downloaded: {destination.name}")
                return True
            else:
                # Remove corrupted/empty file
                destination.unlink()

        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            # Download with progress bar
            with open(destination, 'wb') as f, tqdm(
                    desc=f"📥 {destination.name}",
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

            print(f"✅ Downloaded: {destination.name}")
            return True

        except Exception as e:
            print(f"❌ Error downloading {url}: {e}")
            # Clean up partial download
            if destination.exists():
                destination.unlink()
            return False

    def extract_zip(self, zip_path: Path, extract_to: Path) -> bool:
        """
        Step 4: Extract zip file
        """
        if not zip_path.exists():
            print(f"❌ Zip file not found: {zip_path}")
            return False

        # Check if already extracted
        expected_json_dir = extract_to / zip_path.stem
        if expected_json_dir.exists() and list(expected_json_dir.glob("*.json")):
            print(f"⏭️  Already extracted: {zip_path.name}")
            return True

        try:
            print(f"📦 Extracting: {zip_path.name}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            print(f"✅ Extracted: {zip_path.name}")
            return True

        except Exception as e:
            print(f"❌ Error extracting {zip_path}: {e}")
            return False

    def download_reporter(self, reporter_name: str, keep_zips: bool = False,
                          max_workers: int = 3):
        """
        Complete workflow for one reporter:
        1. Find all zip files
        2. Download them
        3. Extract them
        4. Clean up (optional)
        """
        print(f"\n{'=' * 70}")
        print(f"📚 Processing Reporter: {reporter_name}")
        print(f"{'=' * 70}")

        # Create directories
        reporter_dir = self.output_dir / reporter_name
        reporter_dir.mkdir(exist_ok=True)

        zip_dir = reporter_dir / "zips"
        zip_dir.mkdir(exist_ok=True)

        extracted_dir = reporter_dir / "extracted"
        extracted_dir.mkdir(exist_ok=True)

        # Step 1: Get list of zip files
        zip_files = self.get_zip_files(reporter_name)

        if not zip_files:
            print(f"⚠️  No zip files found for {reporter_name}")
            return

        # Step 2: Download all zips
        print(f"\n📥 Downloading {len(zip_files)} files...")

        download_tasks = [
            (f"{self.base_url}/{reporter_name}/{zip_file}",
             zip_dir / zip_file)
            for zip_file in zip_files
        ]

        successful_downloads = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self.download_file, url, dest): dest
                for url, dest in download_tasks
            }

            for future in as_completed(future_to_file):
                dest = future_to_file[future]
                try:
                    if future.result():
                        successful_downloads.append(dest)
                except Exception as e:
                    print(f"❌ Failed: {dest.name} - {e}")

        print(f"\n✅ Successfully downloaded: {len(successful_downloads)}/{len(zip_files)}")

        # Step 3: Extract all zips
        print(f"\n📦 Extracting {len(successful_downloads)} files...")

        for zip_path in tqdm(successful_downloads, desc="Extracting"):
            self.extract_zip(zip_path, extracted_dir)

        # Step 4: Clean up zips (optional)
        if not keep_zips:
            print(f"\n🗑️  Cleaning up zip files...")
            for zip_path in successful_downloads:
                try:
                    zip_path.unlink()
                    print(f"🗑️  Deleted: {zip_path.name}")
                except Exception as e:
                    print(f"⚠️  Could not delete {zip_path.name}: {e}")

            # Remove zip directory if empty
            try:
                if not any(zip_dir.iterdir()):
                    zip_dir.rmdir()
            except:
                pass

        # Summary
        print(f"\n{'=' * 70}")
        print(f"✅ Completed: {reporter_name}")
        json_files = list(extracted_dir.rglob("*.json"))
        print(f"📊 Total JSON files: {len(json_files)}")
        print(f"📁 Location: {extracted_dir}")
        print(f"{'=' * 70}")

    def download_all_ohio(self, keep_zips: bool = False,
                          max_workers: int = 3,
                          delay_between_reporters: int = 2):
        """
        Complete workflow:
        1. Discover all Ohio reporters
        2. Download each one
        """
        # Step 1: Find all Ohio reporters automatically
        reporters = self.discover_ohio_reporters()

        if not reporters:
            print("❌ No Ohio reporters found!")
            return

        print(f"\n🚀 Starting download of {len(reporters)} reporters")
        print(f"📁 Output directory: {self.output_dir}")

        # Step 2: Download each reporter
        for i, reporter in enumerate(reporters, 1):
            print(f"\n\n{'#' * 70}")
            print(f"# Reporter {i}/{len(reporters)}: {reporter}")
            print(f"{'#' * 70}")

            self.download_reporter(
                reporter_name=reporter,
                keep_zips=keep_zips,
                max_workers=max_workers
            )

            # Be polite to the server
            if i < len(reporters):
                print(f"\n⏸️  Waiting {delay_between_reporters} seconds before next reporter...")
                time.sleep(delay_between_reporters)

        # Final summary
        print(f"\n\n{'=' * 70}")
        print(f"🎉 ALL DOWNLOADS COMPLETE!")
        print(f"{'=' * 70}")

        total_json = 0
        for reporter_dir in self.output_dir.iterdir():
            if reporter_dir.is_dir():
                json_count = len(list(reporter_dir.rglob("*.json")))
                total_json += json_count
                print(f"📚 {reporter_dir.name}: {json_count:,} cases")

        print(f"\n📊 TOTAL: {total_json:,} case files")
        print(f"📁 Location: {self.output_dir}")
        print(f"{'=' * 70}")


def main():
    """
    Run the complete download
    """
    downloader = CaseLawDownloader(
        base_url="https://static.case.law",
        output_dir="./ohio_case_law/data/pre_enriched_input"
    )

    # Download ALL Ohio reporters automatically
    downloader.download_all_ohio(
        keep_zips=False,  # Delete zips after extraction
        max_workers=3,  # 3 parallel downloads (be nice to server)
        delay_between_reporters=2  # 2 second delay between reporters
    )


if __name__ == "__main__":
    main()
