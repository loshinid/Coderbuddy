"""
Clean website generator without autonomous tool calling.
Uses structured JSON output to generate website files.
"""

import json
import logging
import pathlib
import re
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.exceptions import LangChainException
import time
import os

_ = load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeneratedFile(BaseModel):
    """Represents a generated file with path and content."""
    path: str = Field(description="Relative file path from project root")
    content: str = Field(description="Complete file content")
    
    @validator('path')
    def validate_path(cls, v):
        """Ensure path is safe and doesn't escape project directory."""
        if '..' in v or v.startswith('/') or ':' in v:
            raise ValueError(f"Unsafe path detected: {v}")
        return v

class WebsiteProject(BaseModel):
    """Structured output for website generation."""
    project_name: str = Field(description="Name of the website project")
    files: List[GeneratedFile] = Field(description="List of files to generate")
    
    @validator('files')
    def validate_files(cls, v):
        """Ensure at least essential files are present."""
        if not v:
            raise ValueError("At least one file must be generated")
        
        # Check for essential files
        paths = [f.path for f in v]
        if 'index.html' not in paths:
            logger.warning("No index.html file found in generated files")
        
        return v

class WebsiteGenerator:
    """Clean website generator using structured LLM output."""
    
    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        """Initialize the generator with Groq LLM."""
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        # Validate API key format
        if not self.api_key.startswith('gsk_'):
            logger.warning("API key format may be incorrect. Expected format: gsk_...")
        
        self.model_name = model_name
        self.llm = ChatGroq(
            model=model_name,
            api_key=self.api_key,
            temperature=0.7,
            max_tokens=2500,
            timeout=45.0
        )
        
        self.project_root = pathlib.Path(__file__).parent.parent / "generated_project"
        self.project_root.mkdir(exist_ok=True)
        
        logger.info(f"Initialized WebsiteGenerator with model: {model_name}")
        logger.info(f"Project root: {self.project_root}")
    
    def _validate_prompt(self, prompt: str) -> str:
        """Validate and sanitize user prompt."""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        prompt = prompt.strip()
        
        # Check for potentially harmful content
        forbidden_patterns = [
            'password', 'token', 'secret', 'key', 'hack', 'exploit',
            'malware', 'virus', 'script injection', 'xss'
        ]
        
        prompt_lower = prompt.lower()
        for pattern in forbidden_patterns:
            if pattern in prompt_lower:
                logger.warning(f"Potentially harmful pattern detected: {pattern}")
        
        # Limit prompt length
        if len(prompt) > 1000:
            prompt = prompt[:1000] + "..."
            logger.warning("Prompt truncated to 1000 characters")
        
        return prompt
    
    def _get_generation_prompt(self, user_prompt: str) -> str:
        """Generate optimized system prompt for website creation."""
        return f"""Create a modern website for: {user_prompt}

Generate exactly 3 files using these delimiters:

===INDEX.HTML===
[Complete HTML code with semantic structure, meta tags, responsive design]

===STYLES.CSS===
[Complete CSS with modern gradients, animations, flexbox/grid layouts]

===SCRIPT.JS===
[Complete JavaScript with interactive features, smooth interactions]

Requirements:
- Mobile-first responsive design
- Modern gradients and animations  
- Semantic HTML5 tags
- CSS Grid/Flexbox layouts
- Interactive JavaScript features
- Professional appearance

IMPORTANT: Use the exact delimiters shown above. No JSON format."""

    def _parse_delimited_response(self, response_content: str) -> Dict[str, str]:
        """Parse AI response using delimiter-based extraction."""
        logger.info(f"Parsing delimited response, length: {len(response_content)}")
        
        # Clean up the response first
        cleaned_content = self._cleanup_response(response_content)
        logger.info(f"Cleaned response length: {len(cleaned_content)}")
        
        # Extract sections using delimiters
        sections = {}
        
        # Try primary delimiter method
        delimiters = {
            'index.html': '===INDEX.HTML===',
            'styles.css': '===STYLES.CSS===', 
            'script.js': '===SCRIPT.JS==='
        }
        
        for file_name, delimiter in delimiters.items():
            content = self._extract_section(cleaned_content, delimiter)
            if content:
                sections[file_name] = content
                logger.info(f"✅ Extracted {file_name}: {len(content)} chars")
            else:
                logger.warning(f"❌ Missing {file_name} section")
        
        # Fallback extraction if primary method failed
        if len(sections) < 3:
            logger.info("Trying fallback extraction methods...")
            sections = self._fallback_extraction(cleaned_content, sections)
        
        # Generate fallback content for missing sections
        sections = self._ensure_all_sections(sections, cleaned_content)
        
        logger.info(f"Final sections: {list(sections.keys())}")
        return sections
    
    def _cleanup_response(self, content: str) -> str:
        """Clean up AI response by removing markdown and artifacts."""
        # Remove markdown code blocks
        content = re.sub(r'```html\s*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'```css\s*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'```javascript\s*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'```\s*$', '', content)
        
        # Remove explanations and comments outside delimiters
        lines = content.split('\n')
        cleaned_lines = []
        in_delimited_section = False
        
        for line in lines:
            if '===' in line and ('HTML' in line or 'CSS' in line or 'JS' in line):
                in_delimited_section = True
                cleaned_lines.append(line)
            elif in_delimited_section:
                cleaned_lines.append(line)
            elif line.strip().startswith('===INDEX.HTML===') or line.strip().startswith('===STYLES.CSS===') or line.strip().startswith('===SCRIPT.JS==='):
                in_delimited_section = True
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _extract_section(self, content: str, delimiter: str) -> str:
        """Extract content between delimiters."""
        try:
            # Find the delimiter
            start_index = content.find(delimiter)
            if start_index == -1:
                return ""
            
            # Find the next delimiter (end of this section)
            start_index += len(delimiter)
            remaining_content = content[start_index:]
            
            # Find any of the other delimiters to mark the end
            end_delimiters = ['===INDEX.HTML===', '===STYLES.CSS===', '===SCRIPT.JS===']
            end_delimiters.remove(delimiter)  # Remove current delimiter
            
            end_index = len(remaining_content)
            for end_delimiter in end_delimiters:
                end_pos = remaining_content.find(end_delimiter)
                if end_pos != -1 and end_pos < end_index:
                    end_index = end_pos
            
            section_content = remaining_content[:end_index].strip()
            return section_content
            
        except Exception as e:
            logger.error(f"Error extracting section for {delimiter}: {e}")
            return ""
    
    def _fallback_extraction(self, content: str, existing_sections: Dict[str, str]) -> Dict[str, str]:
        """Fallback extraction using regex and pattern matching."""
        sections = existing_sections.copy()
        
        # Try regex extraction for HTML
        if 'index.html' not in sections:
            html_patterns = [
                r'<html[^>]*>.*?</html>',
                r'<!DOCTYPE html>.*?</html>',
                r'<head[^>]*>.*?</head>.*?<body[^>]*>.*?</body>'
            ]
            
            for pattern in html_patterns:
                match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                if match:
                    sections['index.html'] = match.group(0).strip()
                    logger.info(f"✅ Fallback HTML extracted with regex")
                    break
        
        # Try regex extraction for CSS
        if 'styles.css' not in sections:
            css_patterns = [
                r'body\s*\{[^}]*\}',
                r'\.[a-zA-Z][\w-]*\s*\{[^}]*\}',
                r'@media[^{]*\{[^}]*\}'
            ]
            
            # Find all CSS-like content
            css_matches = re.findall(r'\{[^}]*\}', content)
            if css_matches:
                css_content = '\n'.join([f'.element{{match}}' for match in css_matches[:10]])  # Limit to prevent too much content
                sections['styles.css'] = css_content
                logger.info(f"✅ Fallback CSS extracted with regex")
        
        # Try regex extraction for JavaScript
        if 'script.js' not in sections:
            js_patterns = [
                r'function\s+\w+\s*\([^)]*\)\s*\{[^}]*\}',
                r'const\s+\w+\s*=\s*\([^)]*\)\s*=>\s*\{[^}]*\}',
                r'document\.[a-zA-Z]+\([^)]*\)'
            ]
            
            js_content = ""
            for pattern in js_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    js_content += '\n'.join(matches[:5]) + '\n'
            
            if js_content:
                sections['script.js'] = js_content.strip()
                logger.info(f"✅ Fallback JavaScript extracted with regex")
        
        return sections
    
    def _ensure_all_sections(self, sections: Dict[str, str], original_content: str) -> Dict[str, str]:
        """Ensure all required sections exist, generate fallbacks if needed."""
        # Generate fallback HTML if missing
        if 'index.html' not in sections or not sections['index.html'].strip():
            sections['index.html'] = self._generate_fallback_html(original_content)
            logger.info("📝 Generated fallback HTML")
        
        # Generate fallback CSS if missing  
        if 'styles.css' not in sections or not sections['styles.css'].strip():
            sections['styles.css'] = self._generate_fallback_css()
            logger.info("📝 Generated fallback CSS")
        
        # Generate fallback JavaScript if missing
        if 'script.js' not in sections or not sections['script.js'].strip():
            sections['script.js'] = self._generate_fallback_js()
            logger.info("📝 Generated fallback JavaScript")
        
        return sections
    
    def _generate_fallback_html(self, original_content: str) -> str:
        """Generate fallback HTML content."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Website</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <nav>
            <h1>Generated Website</h1>
        </nav>
    </header>
    <main>
        <section class="hero">
            <h2>Welcome to Your Website</h2>
            <p>This is a modern, responsive website generated by AI.</p>
            <button class="cta-button">Get Started</button>
        </section>
    </main>
    <footer>
        <p>&copy; 2024 Generated Website. All rights reserved.</p>
    </footer>
    <script src="script.js"></script>
</body>
</html>"""
    
    def _generate_fallback_css(self) -> str:
        """Generate fallback CSS content."""
        return """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Arial', sans-serif;
    line-height: 1.6;
    color: #333;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

header {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    padding: 1rem 0;
    position: fixed;
    width: 100%;
    top: 0;
    z-index: 1000;
}

nav h1 {
    text-align: center;
    color: white;
    font-size: 1.5rem;
}

main {
    padding-top: 80px;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}

.hero {
    text-align: center;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    padding: 3rem;
    border-radius: 15px;
    max-width: 600px;
    margin: 0 1rem;
}

.hero h2 {
    color: white;
    font-size: 2.5rem;
    margin-bottom: 1rem;
}

.hero p {
    color: rgba(255, 255, 255, 0.8);
    font-size: 1.2rem;
    margin-bottom: 2rem;
}

.cta-button {
    background: linear-gradient(45deg, #ff6b6b, #ee5a24);
    color: white;
    border: none;
    padding: 1rem 2rem;
    font-size: 1.1rem;
    border-radius: 50px;
    cursor: pointer;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.cta-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
}

footer {
    text-align: center;
    padding: 2rem;
    color: rgba(255, 255, 255, 0.6);
    position: absolute;
    bottom: 0;
    width: 100%;
}

@media (max-width: 768px) {
    .hero {
        padding: 2rem;
        margin: 0 0.5rem;
    }
    
    .hero h2 {
        font-size: 2rem;
    }
    
    .hero p {
        font-size: 1rem;
    }
}"""
    
    def _generate_fallback_js(self) -> str:
        """Generate fallback JavaScript content."""
        return """// Generated JavaScript - Interactive Features
document.addEventListener('DOMContentLoaded', function() {
    console.log('Website loaded successfully');
    
    // Smooth scrolling for navigation
    const ctaButton = document.querySelector('.cta-button');
    if (ctaButton) {
        ctaButton.addEventListener('click', function() {
            alert('Welcome to your generated website! This is a placeholder action.');
        });
    }
    
    // Add smooth animations on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe hero section for animation
    const hero = document.querySelector('.hero');
    if (hero) {
        hero.style.opacity = '0';
        hero.style.transform = 'translateY(20px)';
        hero.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(hero);
    }
    
    // Add hover effects to buttons
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
});"""
    
    def _generate_project_name(self, prompt: str) -> str:
        """Generate a project name from the prompt."""
        # Extract key words from prompt
        words = re.findall(r'\b[a-zA-Z]{3,}\b', prompt.lower())
        # Filter out common words
        common_words = {'create', 'modern', 'website', 'page', 'build', 'design', 'make', 'generate'}
        filtered_words = [w for w in words if w not in common_words][:3]
        
        if filtered_words:
            project_name = '-'.join(filtered_words)
        else:
            project_name = "generated-website"
        
        # Sanitize and return
        project_name = ''.join(c for c in project_name if c.isalnum() or c == '-')
        return project_name.lower() or "generated-website"
    
    def _write_files_from_dict(self, sections: Dict[str, str]) -> List[Dict]:
        """Write parsed sections to files."""
        written_files = []
        
        for file_path, content in sections.items():
            try:
                # Validate file content
                if not content:
                    logger.warning(f"Empty content for file: {file_path}")
                    continue
                
                full_path = self.project_root / file_path
                
                # Ensure parent directory exists
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write file content
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                written_files.append({
                    "path": file_path,
                    "size": len(content),
                    "full_path": str(full_path)
                })
                
                logger.info(f"Written file: {file_path} ({len(content)} chars)")
                
            except Exception as e:
                logger.error(f"Failed to write file {file_path}: {e}")
                continue
        
        return written_files

    def generate_website(self, user_prompt: str, max_retries: int = 3) -> Dict:
        """
        Generate a website from user prompt with retry logic.
        
        Args:
            user_prompt: User's website description
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary with generation results
        """
        # Validate input prompt
        validated_prompt = self._validate_prompt(user_prompt)
        # Log request details
        prompt_length = len(validated_prompt)
        estimated_tokens = prompt_length // 4  # Rough estimation: 1 token ≈ 4 chars
        logger.info(f"Starting generation - Prompt length: {prompt_length}, Est. tokens: {estimated_tokens}, Model: {self.model_name}")
        
        for attempt in range(max_retries):
            try:
                # Generate structured output
                logger.info(f"Attempt {attempt + 1}/{max_retries}")
                
                prompt = self._get_generation_prompt(validated_prompt)
                
                # Use regular LLM call with delimiter parsing
                start_time = time.time()
                messages = [
                    SystemMessage(content="You are an expert web developer. Generate code using the exact delimiters provided."),
                    HumanMessage(content=prompt)
                ]
                response = self.llm.invoke(messages)
                generation_time = time.time() - start_time
                
                # Parse the delimited response
                try:
                    content = response.content.strip()
                    logger.info(f"Raw response length: {len(content)} chars")
                    
                    # Parse using delimiter-based extraction
                    parsed_sections = self._parse_delimited_response(content)
                    
                    if not parsed_sections:
                        raise ValueError("No sections parsed from response")
                    
                    logger.info(f"Successfully parsed {len(parsed_sections)} sections")
                    
                except Exception as e:
                    logger.error(f"Delimiter parsing failed: {e}")
                    logger.error(f"Raw content preview: {content[:500]}...")
                    raise ValueError(f"Failed to parse delimited response: {e}")
                
                logger.info(f"LLM response received in {generation_time:.2f}s")
                
                # Generate project name from prompt
                project_name = self._generate_project_name(validated_prompt)
                logger.info(f"Generated project name: {project_name}")
                
                # Create file objects from parsed sections
                files = []
                for file_path, content in parsed_sections.items():
                    files.append({
                        "path": file_path,
                        "content": content,
                        "size": len(content)
                    })
                
                # Write files to disk
                written_files = self._write_files_from_dict(parsed_sections)
                
                logger.info(f"Successfully generated {len(written_files)} files")
                
                return {
                    "success": True,
                    "project_name": project_name,
                    "files": written_files,
                    "generation_time": generation_time,
                    "total_files": len(written_files),
                    "model_used": self.model_name
                }
                
            except (LangChainException, ValueError) as e:
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    return {
                        "success": False,
                        "error": f"Failed after {max_retries} attempts: {str(e)}",
                        "error_type": type(e).__name__,
                        "model_used": self.model_name
                    }
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                error_msg = str(e)
                error_type = type(e).__name__
                
                # Check for rate limit errors
                if "rate limit" in error_msg.lower() or "429" in error_msg:
                    wait_time = 30 + (10 * attempt)  # 30s, 40s, 50s wait
                    logger.warning(f"Rate limit hit on attempt {attempt + 1}, waiting {wait_time}s...")
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("Rate limit exceeded on final attempt")
                        return {
                            "success": False,
                            "error": "API rate limit reached. Please wait and try again.",
                            "error_type": "RateLimitError",
                            "model_used": self.model_name
                        }
                
                # Check for timeout errors
                elif "timeout" in error_msg.lower():
                    logger.warning(f"Timeout on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        time.sleep(5)
                        continue
                    else:
                        return {
                            "success": False,
                            "error": "Request timeout. Please try again.",
                            "error_type": "TimeoutError",
                            "model_used": self.model_name
                        }
                
                logger.error(f"Unexpected error on attempt {attempt + 1}: {error_msg}")
                return {
                    "success": False,
                    "error": f"Unexpected error: {error_msg}",
                    "error_type": error_type,
                    "model_used": self.model_name
                }
    
    def _write_files(self, files: List[GeneratedFile]) -> List[Dict]:
        """Write generated files to disk with validation."""
        written_files = []
        
        for file_obj in files:
            try:
                # Validate file content
                if not file_obj.content:
                    logger.warning(f"Empty content for file: {file_obj.path}")
                    file_obj.content = f"<!-- {file_obj.path} - Generated by CoderBuddy -->\n"
                
                file_path = self.project_root / file_obj.path
                
                # Ensure parent directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Validate file size (prevent extremely large files)
                if len(file_obj.content) > 1000000:  # 1MB limit
                    logger.warning(f"Large file detected: {file_obj.path} ({len(file_obj.content)} chars)")
                    file_obj.content = file_obj.content[:1000000] + "\n<!-- Content truncated due to size limit -->"
                
                # Write file content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_obj.content)
                
                written_files.append({
                    "path": file_obj.path,
                    "size": len(file_obj.content),
                    "full_path": str(file_path)
                })
                
                logger.info(f"Written file: {file_obj.path} ({len(file_obj.content)} chars)")
                
            except Exception as e:
                logger.error(f"Failed to write file {file_obj.path}: {str(e)}")
                raise
        
        return written_files
    
    def get_project_info(self) -> Dict:
        """Get information about the generated project."""
        files = []
        if self.project_root.exists():
            for file_path in self.project_root.rglob('*'):
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.project_root)
                    files.append({
                        "path": str(relative_path),
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime
                    })
        
        return {
            "project_root": str(self.project_root),
            "files": files,
            "total_files": len(files)
        }
    
    def clean_project(self) -> bool:
        """Clean all generated files."""
        try:
            if self.project_root.exists():
                import shutil
                shutil.rmtree(self.project_root)
                self.project_root.mkdir(exist_ok=True)
                logger.info("Cleaned all generated files")
                return True
        except Exception as e:
            logger.error(f"Failed to clean project: {str(e)}")
        return False
