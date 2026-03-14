import yaml
import os
import requests

class DownloadManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.load_config()

    def load_config(self):
        with open(self.config_path, 'r') as file:
            self.config = yaml.safe_load(file)

    def download_arxiv(self, paper_id):
        url = f"https://arxiv.org/pdf/{paper_id}.pdf"
        response = requests.get(url)
        if response.status_code == 200:
            self.save_file(f"{paper_id}.pdf", response.content)
        else:
            print(f"Failed to download paper {paper_id} from arXiv.")

    def download_semantic_scholar(self, paper_id):
        # Placeholder for Semantic Scholar download logic
        print(f"Downloading paper {paper_id} from Semantic Scholar is not yet implemented.")
        
    def save_file(self, filename, content):
        with open(os.path.join(self.config['download_dir'], filename), 'wb') as file:
            file.write(content)

    def orchestrate_downloads(self):
        for paper in self.config['papers']:
            if paper['source'] == 'arxiv':
                self.download_arxiv(paper['id'])
            elif paper['source'] == 'semantic_scholar':
                self.download_semantic_scholar(paper['id'])

if __name__ == "__main__":
    config_path = 'download_config.yaml'
    manager = DownloadManager(config_path)
    manager.orchestrate_downloads()