import os
import re
import json
import logging
import datetime
import markdown
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Union

# Import necessary classes from the existing modules
# These are for type annotations and accessing the repository
from bot import BotType, PromptDoc
from action import is_action_running, get_recent_actions, CommandRegistry, STATE_FILE

# Configure logging
logger = logging.getLogger(__name__)

# Default paths
DEFAULT_PREVIEW_DIR = "preview"
DEFAULT_STATIC_DIR = os.path.join(DEFAULT_PREVIEW_DIR, "static")
DEFAULT_DOCS_DIR = os.path.join(DEFAULT_PREVIEW_DIR, "docs")
DEFAULT_REVISIONS_DIR = os.path.join(DEFAULT_PREVIEW_DIR, "revisions")
DEFAULT_TAGS_DIR = os.path.join(DEFAULT_PREVIEW_DIR, "tags")
DEFAULT_ACTIONS_DIR = os.path.join(DEFAULT_PREVIEW_DIR, "actions")


class HTMLPreviewGenerator:
    """
    Generates HTML previews of the document repository and action history.
    
    This class is responsible for creating a static HTML website that shows
    the current state of the document repository, including documents, revisions,
    tags, and action history.
    """
    
    def __init__(self, doc_repo, preview_dir=DEFAULT_PREVIEW_DIR):
        """
        Initialize the HTML preview generator.
        
        Args:
            doc_repo: The document repository
            preview_dir: Directory to store the HTML preview
        """
        self.doc_repo = doc_repo
        self.preview_dir = preview_dir
        self.static_dir = os.path.join(preview_dir, "static")
        self.docs_dir = os.path.join(preview_dir, "docs")
        self.revisions_dir = os.path.join(preview_dir, "revisions")
        self.tags_dir = os.path.join(preview_dir, "tags")
        self.actions_dir = os.path.join(preview_dir, "actions")
        
        # Ensure directories exist
        os.makedirs(self.preview_dir, exist_ok=True)
        os.makedirs(self.static_dir, exist_ok=True)
        os.makedirs(self.docs_dir, exist_ok=True)
        os.makedirs(self.revisions_dir, exist_ok=True)
        os.makedirs(self.tags_dir, exist_ok=True)
        os.makedirs(self.actions_dir, exist_ok=True)
        
        # Markdown converter
        self.md = markdown.Markdown(extensions=['tables'])
        
        # Cache for document information
        self.doc_cache = {}
        self.all_tags = set()
        
        # Create CSS file
        self._create_css_file()
    
    def _create_css_file(self):
        """Create a CSS file for styling the HTML pages."""
        css_content = """
        :root {
            --primary-color: #2c3e50;
            --secondary-color: #3498db;
            --background-color: #f9f9f9;
            --text-color: #333;
            --link-color: #3498db;
            --border-color: #ddd;
            --success-color: #2ecc71;
            --warning-color: #f39c12;
            --danger-color: #e74c3c;
            --info-color: #3498db;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--background-color);
            margin: 0;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 15px;
        }
        
        header {
            background-color: var(--primary-color);
            color: white;
            padding: 1rem;
            margin-bottom: 2rem;
            border-radius: 5px;
        }
        
        header h1 {
            margin: 0;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: var(--primary-color);
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }
        
        a {
            color: var(--link-color);
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        .card {
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        .card-header {
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .card-title {
            margin: 0;
            color: var(--primary-color);
        }
        
        .status-box {
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 1.5rem;
        }
        
        .status-running {
            background-color: var(--info-color);
            color: white;
        }
        
        .status-success {
            background-color: var(--success-color);
            color: white;
        }
        
        .status-failure {
            background-color: var(--danger-color);
            color: white;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1.5rem;
        }
        
        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        
        th {
            background-color: var(--primary-color);
            color: white;
        }
        
        tr:nth-child(even) {
            background-color: rgba(0, 0, 0, 0.05);
        }
        
        .nav {
            display: flex;
            list-style: none;
            padding: 0;
            margin: 0 0 1.5rem 0;
            background-color: var(--primary-color);
            border-radius: 5px;
        }
        
        .nav li {
            padding: 0;
        }
        
        .nav a {
            display: block;
            padding: 0.75rem 1rem;
            color: white;
            text-decoration: none;
        }
        
        .nav a:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
        
        .tag {
            display: inline-block;
            background-color: var(--secondary-color);
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 3px;
            margin-right: 0.5rem;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
        }
        
        .tag a {
            color: white;
        }
        
        .document-content {
            background-color: white;
            padding: 1.5rem;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .properties-table {
            width: 100%;
            margin-bottom: 1.5rem;
        }
        
        .chapter-list, .document-list {
            list-style: none;
            padding: 0;
        }
        
        .chapter-list li, .document-list li {
            margin-bottom: 0.5rem;
            padding: 0.75rem;
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        .chapter-list li:hover, .document-list li:hover {
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
        }
        
        .actions-list {
            list-style: none;
            padding: 0;
        }
        
        .actions-list li {
            margin-bottom: 0.5rem;
            padding: 0.75rem;
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            display: flex;
            justify-content: space-between;
        }
        
        .actions-list .action-status {
            font-weight: bold;
            padding: 0.25rem 0.5rem;
            border-radius: 3px;
        }
        
        .actions-list .status-success {
            background-color: var(--success-color);
        }
        
        .actions-list .status-failure {
            background-color: var(--danger-color);
        }
        
        .actions-list .status-running {
            background-color: var(--info-color);
        }
        
        footer {
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border-color);
            text-align: center;
            font-size: 0.875rem;
            color: #777;
        }
        """
        
        css_path = os.path.join(self.static_dir, "style.css")
        with open(css_path, "w") as css_file:
            css_file.write(css_content)
    
    def _create_html_template(self, title, body, active_nav=None):
        """
        Create an HTML template with navigation and common elements.
        
        Args:
            title: Page title
            body: Page content
            active_nav: Active navigation item
            
        Returns:
            Complete HTML page
        """
        # Determine the proper path prefix based on the depth of the file
        # For index.html at the root, we need no prefix
        # For other files in subdirectories, we need to go up one level
        path_prefix = ""
        if active_nav and active_nav != "home":
            path_prefix = "../"
        
        nav_items = [
            {"id": "home", "name": "Home", "url": f"{path_prefix}index.html"},
            {"id": "docs", "name": "Documents", "url": f"{path_prefix}index.html"},
            {"id": "tags", "name": "Tags", "url": f"{path_prefix}tags/index.html"},
            {"id": "actions", "name": "Actions", "url": f"{path_prefix}actions/index.html"},
            {"id": "bots", "name": "Bots", "url": f"{path_prefix}bots/index.html"}
        ]
        
        nav_html = '<ul class="nav">'
        for item in nav_items:
            active_class = ' class="active"' if item["id"] == active_nav else ''
            nav_html += f'<li{active_class}><a href="{item["url"]}">{item["name"]}</a></li>'
        nav_html += '</ul>'
        
        html = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - BookBot Preview</title>
        <link rel="stylesheet" href="{path_prefix}static/style.css">
    </head>
    <body>
        <div class="container">
            <header>
                <h1>BookBot Preview</h1>
            </header>
            {nav_html}
            <main>
                <h1>{title}</h1>
                {body}
            </main>
            <footer>
                <p>Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </footer>
        </div>
    </body>
    </html>
    """
        return html
    
    def generate_preview(self):
        """Generate the complete HTML preview."""
        logger.info("Generating HTML preview...")
        
        # Generate index page
        self._generate_index()
        
        # Generate document pages
        self._generate_document_pages()
        
        # Generate tag pages
        self._generate_tag_pages()
        
        # Generate action pages
        self._generate_action_pages()
        
        # Generate bot pages
        self._generate_bot_pages()
        
        logger.info(f"HTML preview generated in {self.preview_dir}")
    
    def _generate_index(self):
        """Generate the index page."""
        # Get current action status
        action_status_html = self._get_action_status_html()
        
        # Get document lists (chapters and others)
        chapters, other_docs = self._get_document_lists()
        
        # Create chapter list
        chapter_list_html = '<h2>Chapters</h2>'
        if chapters:
            chapter_list_html += '<ul class="chapter-list">'
            for doc_name, doc_info in chapters:
                token_info = ""
                if "output_tokens" in doc_info["properties"]:
                    token_info = f" ({doc_info['properties']['output_tokens']} tokens)"
                chapter_list_html += f'<li><a href="docs/{doc_name}.html">{doc_name}</a>{token_info}</li>'
            chapter_list_html += '</ul>'
        else:
            chapter_list_html += '<p>No chapters found.</p>'
        
        # Create other documents list
        other_docs_html = '<h2>Other Documents</h2>'
        if other_docs:
            other_docs_html += '<ul class="document-list">'
            for doc_name, doc_info in other_docs:
                doc_type = doc_info["properties"].get("type", "unknown")
                other_docs_html += f'<li><a href="docs/{doc_name}.html">{doc_name}</a> ({doc_type})</li>'
            other_docs_html += '</ul>'
        else:
            other_docs_html += '<p>No other documents found.</p>'
        
        # Combine all sections
        body = f"""
        {action_status_html}
        
        <div class="card">
            {chapter_list_html}
        </div>
        
        <div class="card">
            {other_docs_html}
        </div>
        
        <div class="card">
            <h2>Quick Links</h2>
            <ul>
                <li><a href="tags/index.html">All Tags</a></li>
                <li><a href="actions/index.html">Action History</a></li>
                <li><a href="bots/index.html">Available Bots</a></li>
            </ul>
        </div>
        """
        
        # Create the HTML page
        html = self._create_html_template("Home", body, active_nav="home")
        
        # Write to file
        index_path = os.path.join(self.preview_dir, "index.html")
        with open(index_path, "w") as index_file:
            index_file.write(html)
    
    def _get_action_status_html(self):
        """Get HTML for the current action status."""
        action_info = is_action_running()
        
        if not action_info:
            return '<div class="status-box"><p>No action currently running.</p></div>'
        
        command = action_info.get("command", "Unknown")
        args = action_info.get("args", [])
        args_str = ' '.join(args) if args else ""
        status = action_info.get("status", "running")
        current_step = action_info.get("current_step", "Unknown")
        start_time = action_info.get("start_time", "Unknown")
        
        return f"""
        <div class="status-box status-running">
            <h2>Current Action: {command}</h2>
            <p><strong>Arguments:</strong> {args_str}</p>
            <p><strong>Status:</strong> {status}</p>
            <p><strong>Current Step:</strong> {current_step}</p>
            <p><strong>Started:</strong> {start_time}</p>
        </div>
        """
    
    def _get_document_lists(self):
        """
        Get sorted lists of chapters and other documents.
        
        Returns:
            Tuple of (chapters, other_docs) where each is a list of (doc_name, doc_info) tuples
        """
        chapters = []
        other_docs = []
        
        # Get all documents
        for doc_name in self.doc_repo.list_docs():
            doc = self.doc_repo.get_doc(doc_name)
            if not doc:
                continue
            
            # Get document properties and text
            properties = doc.get_properties()
            text = doc.get_text()
            
            # Store in cache
            self.doc_cache[doc_name] = {
                "properties": properties,
                "text": text,
                "versions": doc.get_versions()
            }
            
            # Check if it's a chapter
            doc_type = properties.get("type", "").lower()
            if doc_type == "chapter":
                order = properties.get("order", 9999)
                chapters.append((doc_name, self.doc_cache[doc_name], order))
            else:
                other_docs.append((doc_name, self.doc_cache[doc_name]))
        
        # Sort chapters by order
        chapters.sort(key=lambda x: x[2])
        chapters = [(name, info) for name, info, _ in chapters]
        
        # Sort other documents by name
        other_docs.sort(key=lambda x: x[0])
        
        return chapters, other_docs
    
    def _generate_document_pages(self):
        """Generate HTML pages for all documents."""
        logger.info("Generating document pages...")
        
        # Process each document
        for doc_name, doc_info in self.doc_cache.items():
            properties = doc_info["properties"]
            text = doc_info["text"]
            versions = doc_info["versions"]
            
            # Convert text to HTML
            html_content = self._convert_markdown_to_html(text)
            
            # Process document links and tags
            html_content = self._process_document_links(html_content)
            html_content = self._process_tags(html_content)
            
            # Generate properties table
            properties_html = self._generate_properties_table(properties, doc_name)
            
            # Add revision history link
            revision_link = f'<p><a href="../revisions/{doc_name}.html">View Revision History</a></p>'
            
            # Combine all sections
            body = f"""
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">{doc_name}</h2>
                </div>
                {properties_html}
                {revision_link}
            </div>
            
            <div class="document-content">
                {html_content}
            </div>
            """
            
            # Create the HTML page
            html = self._create_html_template(doc_name, body, active_nav="docs")
            
            # Write to file
            doc_path = os.path.join(self.docs_dir, f"{doc_name}.html")
            with open(doc_path, "w") as doc_file:
                doc_file.write(html)
            
            # Generate revision pages
            self._generate_revision_page(doc_name, versions)
            
            # Generate version pages
            for version in versions:
                self._generate_version_page(doc_name, version)
    
    def _convert_markdown_to_html(self, markdown_text):
        """
        Convert Markdown text to HTML.
        
        Args:
            markdown_text: Markdown text to convert
            
        Returns:
            HTML content
        """
        try:
            # Convert Markdown to HTML
            html = self.md.convert(markdown_text)
            
            # Reset the converter for the next document
            self.md.reset()
            
            return html
        except Exception as e:
            logger.error(f"Error converting Markdown to HTML: {e}")
            return f"<p>Error rendering Markdown: {e}</p><pre>{markdown_text}</pre>"
    
    def _generate_properties_table(self, properties, doc_name):
        """
        Generate HTML table for document properties.
        
        Args:
            properties: Dictionary of properties
            doc_name: Document name for linking
            
        Returns:
            HTML table
        """
        if not properties:
            return "<p>No properties found.</p>"
        
        html = '<h3>Properties</h3><table class="properties-table"><tr><th>Property</th><th>Value</th></tr>'
        
        for key, value in sorted(properties.items()):
            # Convert document references to links
            if isinstance(value, str):
                value = self._convert_doc_refs_to_links(value)
            
            html += f"<tr><td>{key}</td><td>{value}</td></tr>"
        
        html += "</table>"
        return html
    
    # Fix for _process_document_links
    def _process_document_links(self, html_content):
        """
        Process document links in HTML content.
        
        Args:
            html_content: HTML content to process
            
        Returns:
            Processed HTML content
        """
        # This is a simplified approach; in a real implementation, you'd want
        # to use a proper HTML parser to avoid breaking HTML tags
        doc_names = list(self.doc_cache.keys())
        
        # Sort by length (longest first) to avoid partial matches
        doc_names.sort(key=len, reverse=True)
        
        for doc_name in doc_names:
            # Look for the document name in a word boundary
            pattern = r'\b(' + re.escape(doc_name) + r')(?!\w)'
            html_content = re.sub(
                pattern,
                r'<a href="docs/\1.html">\1</a>',  # Remove the ../ prefix
                html_content
            )
        
        return html_content
    # Fix for _process_tags
    def _process_tags(self, html_content):
        """
        Process tags in HTML content.
        
        Args:
            html_content: HTML content to process
            
        Returns:
            Processed HTML content with tag links
        """
        # Find all tags (# followed by alphanumeric characters) but not at the beginning of a line
        tags = re.findall(r'(?<!^)#(\w+)', html_content, re.MULTILINE)
        self.all_tags.update(tags)
        
        # Replace tags with links (not at beginning of line)
        for tag in tags:
            pattern = r'(?<!\n)#(' + re.escape(tag) + r')\b'
            html_content = re.sub(
                pattern,
                r'<a href="tags/\1.html" class="tag">#\1</a>',  # Remove the ../ prefix
                html_content
            )
        
        return html_content
    
    def _convert_doc_refs_to_links(self, text):
        """
        Convert document and bot references to links.
        
        Args:
            text: Text to process
            
        Returns:
            Processed text with document and bot links
        """
        # Check for doc#version pattern first (most specific)
        doc_version_pattern = r'(\w+)#(\d+)'
        
        def replace_doc_version(match):
            doc_name = match.group(1)
            version = match.group(2)
            if doc_name in self.doc_cache:
                return f'<a href="../revisions/{doc_name}_v{version}.html">{doc_name}#{version}</a>'
            return match.group(0)
        
        text = re.sub(doc_version_pattern, replace_doc_version, text)
        
        # Get list of all bot names (documents with type "prompt")
        bot_names = []
        for doc_name, doc_info in self.doc_cache.items():
            properties = doc_info.get("properties", {})
            if properties.get("type") == "prompt":
                bot_names.append(doc_name)
        
        # Sort by length (longest first) to avoid partial matches
        bot_names.sort(key=len, reverse=True)
        
        # Check for bot names
        for bot_name in bot_names:
            pattern = r'\b(' + re.escape(bot_name) + r')(?!\w|#)'
            text = re.sub(pattern, r'<a href="../bots/\1.html">\1</a>', text)
        
        # Check for plain document names (do this last to avoid overriding more specific patterns)
        doc_names = list(self.doc_cache.keys())
        for doc_name in doc_names:
            # Skip bot names as we've already processed them
            if doc_name in bot_names:
                continue
                
            pattern = r'\b(' + re.escape(doc_name) + r')(?!\w|#)'
            text = re.sub(pattern, r'<a href="../docs/\1.html">\1</a>', text)
        
        return text
    def _generate_revision_page(self, doc_name, versions):
        """
        Generate revision history page for a document.
        
        Args:
            doc_name: Document name
            versions: List of version numbers
        """
        versions_list = '<h2>Revisions</h2><ul class="revisions-list">'
        
        # Sort versions in descending order
        sorted_versions = sorted(versions, reverse=True)
        
        for version in sorted_versions:
            versions_list += f'<li><a href="{doc_name}_v{version}.html">Version {version}</a></li>'
        
        versions_list += '</ul>'
        
        # Create the HTML page
        body = f"""
        <div class="card">
            <div class="card-header">
                <h2 class="card-title">Revision History for {doc_name}</h2>
            </div>
            <p><a href="../docs/{doc_name}.html">Back to current version</a></p>
            {versions_list}
        </div>
        """
        
        html = self._create_html_template(f"Revision History - {doc_name}", body, active_nav="docs")
        
        # Write to file
        revision_path = os.path.join(self.revisions_dir, f"{doc_name}.html")
        with open(revision_path, "w") as revision_file:
            revision_file.write(html)
    
    def _generate_version_page(self, doc_name, version):
        """
        Generate page for a specific document version.
        
        Args:
            doc_name: Document name
            version: Version number
        """
        doc = self.doc_repo.get_doc(doc_name)
        if not doc:
            return
        
        try:
            properties = doc.get_version_properties(version)
            text = doc.get_version_text(version)
            
            # Convert text to HTML
            html_content = self._convert_markdown_to_html(text)
            
            # Process document links and tags
            html_content = self._process_document_links(html_content)
            html_content = self._process_tags(html_content)
            
            # Generate properties table
            properties_html = self._generate_properties_table(properties, doc_name)
            
            # Combine all sections
            body = f"""
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">{doc_name} - Version {version}</h2>
                </div>
                <p><a href="{doc_name}.html">Back to Revision History</a> | <a href="../docs/{doc_name}.html">Back to Current Version</a></p>
                {properties_html}
            </div>
            
            <div class="document-content">
                {html_content}
            </div>
            """
            
            # Create the HTML page
            html = self._create_html_template(f"{doc_name} - Version {version}", body, active_nav="docs")
            
            # Write to file
            version_path = os.path.join(self.revisions_dir, f"{doc_name}_v{version}.html")
            with open(version_path, "w") as version_file:
                version_file.write(html)
                
        except Exception as e:
            logger.error(f"Error generating version page for {doc_name} v{version}: {e}")
    
    def _generate_tag_pages(self):
        """Generate tag index and individual tag pages."""
        logger.info("Generating tag pages...")
        
        # Generate tag index
        tag_index_html = '<h2>All Tags</h2>'
        
        if self.all_tags:
            tag_index_html += '<div class="tags-container">'
            for tag in sorted(self.all_tags):
                tag_index_html += f'<a href="{tag}.html" class="tag">#{tag}</a>'
            tag_index_html += '</div>'
        else:
            tag_index_html += '<p>No tags found.</p>'
        
        # Create the HTML page
        body = f"""
        <div class="card">
            <div class="card-header">
                <h2 class="card-title">Tags</h2>
            </div>
            {tag_index_html}
        </div>
        """
        
        html = self._create_html_template("Tags", body, active_nav="tags")
        
        # Write to file
        tag_index_path = os.path.join(self.tags_dir, "index.html")
        with open(tag_index_path, "w") as tag_index_file:
            tag_index_file.write(html)
        
        # Generate individual tag pages
        for tag in self.all_tags:
            self._generate_tag_page(tag)
    
    def _generate_tag_page(self, tag):
        """
        Generate page for a specific tag.
        
        Args:
            tag: Tag name
        """
        # Find all documents with this tag
        tag_docs = []
        
        for doc_name, doc_info in self.doc_cache.items():
            text = doc_info["text"]
            # Look for the tag (not at beginning of line)
            if re.search(r'(?<!\n)#' + re.escape(tag) + r'\b', text, re.MULTILINE):
                tag_docs.append(doc_name)
        
        # Create document list
        doc_list_html = '<h2>Documents with this tag</h2>'
        
        if tag_docs:
            doc_list_html += '<ul class="document-list">'
            for doc_name in sorted(tag_docs):
                doc_list_html += f'<li><a href="../docs/{doc_name}.html">{doc_name}</a></li>'
            doc_list_html += '</ul>'
        else:
            doc_list_html += '<p>No documents found with this tag.</p>'
        
        # Create the HTML page
        body = f"""
        <div class="card">
            <div class="card-header">
                <h2 class="card-title">Tag: #{tag}</h2>
            </div>
            <p><a href="index.html">Back to All Tags</a></p>
            {doc_list_html}
        </div>
        """
        
        html = self._create_html_template(f"Tag - #{tag}", body, active_nav="tags")
        
        # Write to file
        tag_path = os.path.join(self.tags_dir, f"{tag}.html")
        with open(tag_path, "w") as tag_file:
            tag_file.write(html)
        
    def _generate_action_pages(self):
            """Generate action index and individual action pages."""
            logger.info("Generating action pages...")
            
            # Get recent actions
            actions = get_recent_actions(count=100)  # Get up to 100 recent actions
            
            # Generate action index
            action_index_html = '<h2>Recent Actions</h2>'
            
            if actions:
                action_index_html += '<ul class="actions-list">'
                for i, action in enumerate(actions):
                    action_file = f"action_{i}.html"
                    command = action.get("command", "Unknown")
                    args = action.get("args", [])
                    args_str = ' '.join(args) if args else ""
                    status = action.get("status", "unknown")
                    start_time = action.get("start_time", "Unknown")
                    end_time = action.get("end_time", "Unknown")
                    
                    status_class = {
                        "running": "status-running",
                        "success": "status-success", 
                        "failure": "status-failure"
                    }.get(status.lower(), "")
                    
                    action_index_html += f"""
                    <li>
                        <div>
                            <a href="{action_file}">{command} {args_str}</a>
                            <div>Started: {start_time}</div>
                        </div>
                        <span class="action-status {status_class}">{status}</span>
                    </li>
                    """
                    
                    # Generate individual action page
                    self._generate_action_page(action, i)
                
                action_index_html += '</ul>'
            else:
                action_index_html += '<p>No actions found.</p>'
            
            # Create the HTML page
            body = f"""
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Action History</h2>
                </div>
                {action_index_html}
            </div>
            """
            
            html = self._create_html_template("Actions", body, active_nav="actions")
            
            # Write to file
            action_index_path = os.path.join(self.actions_dir, "index.html")
            with open(action_index_path, "w") as action_index_file:
                action_index_file.write(html)
        
    def _generate_action_page(self, action, index):
        """
        Generate page for a specific action.
        
        Args:
            action: Action data
            index: Index for filename
        """
        command = action.get("command", "Unknown")
        args = action.get("args", [])
        args_str = ' '.join(args) if args else ""
        status = action.get("status", "unknown")
        start_time = action.get("start_time", "Unknown")
        end_time = action.get("end_time", "Unknown")
        pid = action.get("pid", "Unknown")
        input_docs = action.get("input_docs", [])
        output_docs = action.get("output_docs", [])
        token_usage = action.get("token_usage", {})
        
        status_class = {
            "running": "status-running",
            "success": "status-success", 
            "failure": "status-failure"
        }.get(status.lower(), "")
        
        # Create input documents list
        input_docs_html = "<h3>Input Documents</h3>"
        if input_docs:
            input_docs_html += "<ul>"
            for doc in input_docs:
                input_docs_html += f'<li><a href="../docs/{doc}.html">{doc}</a></li>'
            input_docs_html += "</ul>"
        else:
            input_docs_html += "<p>No input documents.</p>"
        
        # Create output documents list
        output_docs_html = "<h3>Output Documents</h3>"
        if output_docs:
            output_docs_html += "<ul>"
            for doc in output_docs:
                output_docs_html += f'<li><a href="../docs/{doc}.html">{doc}</a></li>'
            output_docs_html += "</ul>"
        else:
            output_docs_html += "<p>No output documents.</p>"
        
        # Create token usage info
        token_usage_html = "<h3>Token Usage</h3>"
        input_tokens = token_usage.get("input_tokens", 0)
        output_tokens = token_usage.get("output_tokens", 0)
        token_usage_html += f"""
        <table>
            <tr><th>Input Tokens</th><td>{input_tokens}</td></tr>
            <tr><th>Output Tokens</th><td>{output_tokens}</td></tr>
            <tr><th>Total Tokens</th><td>{input_tokens + output_tokens}</td></tr>
        </table>
        """
        
        # Create the HTML page
        body = f"""
        <div class="card">
            <div class="card-header">
                <h2 class="card-title">{command} {args_str}</h2>
                <span class="action-status {status_class}">{status}</span>
            </div>
            
            <table>
                <tr><th>Start Time</th><td>{start_time}</td></tr>
                <tr><th>End Time</th><td>{end_time}</td></tr>
                <tr><th>Process ID</th><td>{pid}</td></tr>
                <tr><th>Status</th><td>{status}</td></tr>
            </table>
            
            {input_docs_html}
            {output_docs_html}
            {token_usage_html}
        </div>
        """
        
        html = self._create_html_template(f"Action - {command}", body, active_nav="actions")
        
        # Write to file
        action_path = os.path.join(self.actions_dir, f"action_{index}.html")
        with open(action_path, "w") as action_file:
            action_file.write(html)
    
    def _generate_bot_pages(self):
        """Generate bot index and individual bot pages."""
        logger.info("Generating bot pages...")
        
        # Create bots directory
        bots_dir = os.path.join(self.preview_dir, "bots")
        os.makedirs(bots_dir, exist_ok=True)
        
        # Find all bot documents
        bots = []
        for doc_name in self.doc_repo.list_docs():
            doc = self.doc_repo.get_doc(doc_name)
            if not doc:
                continue
            
            properties = doc.get_properties()
            if properties.get("type") == "prompt":
                try:
                    # Try to create a PromptDoc to see if it's valid
                    prompt_doc = PromptDoc(doc)
                    bots.append((doc_name, prompt_doc))
                except:
                    # Not a valid bot, skip it
                    continue
        
        # Generate bot index
        bot_index_html = '<h2>Available Bots</h2>'
        
        if bots:
            bot_index_html += '<ul class="document-list">'
            for doc_name, prompt_doc in bots:
                bot_type = prompt_doc.bot_type.name
                llm = prompt_doc.llm
                bot_index_html += f'<li><a href="{doc_name}.html">{doc_name}</a> ({bot_type} - {llm})</li>'
                
                # Generate individual bot page
                self._generate_bot_page(doc_name, prompt_doc, bots_dir)
            
            bot_index_html += '</ul>'
        else:
            bot_index_html += '<p>No bots found.</p>'
        
        # Create the HTML page
        body = f"""
        <div class="card">
            <div class="card-header">
                <h2 class="card-title">Bots</h2>
            </div>
            {bot_index_html}
        </div>
        """
        
        html = self._create_html_template("Bots", body, active_nav="bots")
        
        # Write to file
        bot_index_path = os.path.join(bots_dir, "index.html")
        with open(bot_index_path, "w") as bot_index_file:
            bot_index_file.write(html)
    
    def _generate_bot_page(self, doc_name, prompt_doc, bots_dir):
        """
        Generate page for a specific bot.
        
        Args:
            doc_name: Bot document name
            prompt_doc: PromptDoc instance
            bots_dir: Directory for bot pages
        """
        doc = prompt_doc.doc
        bot_type = prompt_doc.bot_type.name
        llm = prompt_doc.llm
        raw_llm = prompt_doc._raw_llm
        temperature = prompt_doc.temperature
        expected_length = prompt_doc.expected_length
        system_prompt = prompt_doc.system_prompt
        main_prompt = prompt_doc.main_prompt
        continuation_prompt = prompt_doc.continuation_prompt
        required_vars = list(prompt_doc.bot_type.required_vars)
        
        # Create configuration table
        config_html = "<h3>Configuration</h3>"
        config_html += """
        <table>
            <tr><th>Type</th><td>{0}</td></tr>
            <tr><th>LLM</th><td>{1} ({2})</td></tr>
            <tr><th>Temperature</th><td>{3}</td></tr>
            <tr><th>Expected Length</th><td>{4} words</td></tr>
        </table>
        """.format(bot_type, llm, raw_llm, temperature, expected_length)
        
        # Create required variables list
        vars_html = "<h3>Required Variables</h3>"
        if required_vars:
            vars_html += "<ul>"
            for var in required_vars:
                vars_html += f"<li>{var}</li>"
            vars_html += "</ul>"
        else:
            vars_html += "<p>No variables required.</p>"
        
        # Create prompt sections
        prompts_html = "<h3>Prompts</h3>"
        
        prompts_html += "<h4>System Prompt</h4>"
        prompts_html += f"<pre>{system_prompt}</pre>"
        
        prompts_html += "<h4>Main Prompt</h4>"
        prompts_html += f"<pre>{main_prompt}</pre>"
        
        prompts_html += "<h4>Continuation Prompt</h4>"
        prompts_html += f"<pre>{continuation_prompt}</pre>"
        
        # Create the HTML page
        body = f"""
        <div class="card">
            <div class="card-header">
                <h2 class="card-title">Bot: {doc_name}</h2>
            </div>
            
            {config_html}
            {vars_html}
            {prompts_html}
        </div>
        """
        
        html = self._create_html_template(f"Bot - {doc_name}", body, active_nav="bots")
        
        # Write to file
        bot_path = os.path.join(bots_dir, f"{doc_name}.html")
        with open(bot_path, "w") as bot_file:
            bot_file.write(html)


# Utility functions for parsing markdown documents

def parse_markdown_properties(content):
    """
    Parse properties from markdown content.
    
    Args:
        content: Markdown content to parse
        
    Returns:
        Tuple of (properties, text) where properties is a dictionary
    """
    properties = {}
    
    # Check if the content starts with --- delimiter
    if content.startswith('---'):
        # Split at the second --- delimiter
        parts = content.split('---', 2)
        if len(parts) >= 3:
            properties_text = parts[1]
            text = parts[2].strip()
            
            # Parse properties
            for line in properties_text.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    properties[key.strip()] = value.strip()
            
            return properties, text
    
    # If not, use the old style properties
    lines = content.split('\n')
    text_lines = []
    in_properties = True
    
    for line in lines:
        if in_properties:
            if ':' in line:
                key, value = line.split(':', 1)
                properties[key.strip()] = value.strip()
            else:
                in_properties = False
                text_lines.append(line)
        else:
            text_lines.append(line)
    
    text = '\n'.join(text_lines)
    
    # Handle case when properties are followed by ---
    if '---' in text:
        text = text.split('---', 1)[1].strip()
    
    return properties, text


def extract_tags_from_text(text):
    """
    Extract all tags from text.
    
    Args:
        text: Text to extract tags from
        
    Returns:
        Set of tags
    """
    # Find all tags not at the beginning of a line
    tags = re.findall(r'(?<!\n)#(\w+)', text, re.MULTILINE)
    return set(tags)


def extract_document_refs(text, doc_names):
    """
    Extract document references from text.
    
    Args:
        text: Text to extract references from
        doc_names: List of valid document names
        
    Returns:
        Set of document names
    """
    refs = set()
    
    # Check for doc#version pattern
    doc_version_pattern = r'(\w+)#(\d+)'
    doc_refs = re.findall(doc_version_pattern, text)
    
    for doc_name, _ in doc_refs:
        if doc_name in doc_names:
            refs.add(doc_name)
    
    # Check for plain document names
    for doc_name in doc_names:
        pattern = r'\b(' + re.escape(doc_name) + r')(?!\w|#)'
        if re.search(pattern, text):
            refs.add(doc_name)
    
    return refs


# Main function to generate preview

def generate_preview(doc_repo, preview_dir=DEFAULT_PREVIEW_DIR):
    """
    Generate HTML preview for a document repository.
    
    Args:
        doc_repo: Document repository
        preview_dir: Directory to store the preview
    """
    generator = HTMLPreviewGenerator(doc_repo, preview_dir)
    generator.generate_preview()
    
    logger.info(f"HTML preview generated in {preview_dir}")
    return preview_dir



def main():
    """Main function to create the demo and generate preview."""
    # Create a directory for the demo in the current directory
    import os
    current_dir = os.getcwd()
    demo_dir = os.path.join(current_dir, "preview_demo_files")
    preview_dir = os.path.join(demo_dir, "preview")
    actions_dir = os.path.join(demo_dir, "actions")
    
    # Create the directories
    os.makedirs(demo_dir, exist_ok=True)
    os.makedirs(actions_dir, exist_ok=True)
    
    try:
        # Create DocRepo with demo documents
        repo = MockDocRepo()
        for doc in create_demo_docs():
            repo.add_doc(doc)
        
        logger.info(f"Created mock DocRepo with {len(repo.list_docs())} documents")
        
        # Create mock actions directory
        create_mock_actions_dir(actions_dir)
        
        # Create mock state file for a currently running action
        state_file = os.path.join(demo_dir, "state.json")
        create_mock_state_file(state_file)
        
        # Import the preview generator
        from preview import generate_preview
        
        # Monkey patch for the demo
        import preview
        preview.STATE_FILE = state_file
        preview.get_recent_actions = lambda count=10, actions_dir=actions_dir: [
            json.load(open(os.path.join(actions_dir, f))) 
            for f in sorted(os.listdir(actions_dir), reverse=True)[:count]
            if f.endswith('.json')
        ]
        
        # Generate the preview
        logger.info("Generating HTML preview...")
        preview_path = generate_preview(repo, preview_dir)
        
        # Print success message with clear instructions
        print("\n" + "="*80)
        print(f"Preview generated successfully!")
        print(f"Open this file in your web browser: {os.path.join(preview_path, 'index.html')}")
        print("="*80)
        
        # Only clean up if explicitly requested
        if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
            print(f"Cleaning up demo files from {demo_dir}")
            shutil.rmtree(demo_dir)
        else:
            print(f"All files have been saved to: {demo_dir}")
            print("Run with --cleanup flag if you want to remove the files after viewing")
        
    except Exception as e:
        logger.error(f"Error generating preview: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()