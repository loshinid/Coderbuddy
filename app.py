"""
FastAPI backend for CoderBuddy AI website generator.
Provides REST API endpoints for website generation.
"""

import os
import logging
import zipfile
import io
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import uvicorn
from agent.generator import WebsiteGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CoderBuddy AI Website Generator",
    description="Generate modern websites from text prompts using AI",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global generator instance
generator: Optional[WebsiteGenerator] = None

# Paths for static files
FRONTEND_DIR = Path("frontend")
STATIC_DIR = Path("frontend")
GENERATED_DIR = Path("generated_project")
FRONTEND_INDEX = FRONTEND_DIR / "index.html"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    global generator
    try:
        generator = WebsiteGenerator()
        logger.info("Website generator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize generator: {str(e)}")
        generator = None
    
    # Validate frontend files exist
    if not FRONTEND_INDEX.exists():
        logger.warning(f"Frontend index file not found at {FRONTEND_INDEX}")
    else:
        logger.info(f"Frontend files found at {FRONTEND_DIR}")
    
    yield
    
    # Shutdown
    logger.info("Application shutting down")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="CoderBuddy AI Website Generator",
    description="Generate modern websites from text prompts using AI",
    version="2.0.0",
    lifespan=lifespan
)

# Pydantic models for API
class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=1000, description="Website description prompt")
    model: str = Field(default="llama-3.1-8b-instant", description="Groq model to use")

class GenerateResponse(BaseModel):
    success: bool
    project_name: Optional[str] = None
    files: Optional[List[Dict]] = None
    generation_time: Optional[float] = None
    total_files: Optional[int] = None
    error: Optional[str] = None
    error_type: Optional[str] = None

class ProjectInfo(BaseModel):
    project_root: str
    files: List[Dict]
    total_files: int

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    logger.info(f"Static files mounted at /static from {STATIC_DIR}")
else:
    logger.error(f"Static directory not found: {STATIC_DIR}")

# Mount generated projects for preview
if GENERATED_DIR.exists():
    GENERATED_DIR.mkdir(exist_ok=True)
    app.mount("/generated", StaticFiles(directory=str(GENERATED_DIR)), name="generated")
    logger.info(f"Generated projects mounted at /generated from {GENERATED_DIR}")
else:
    logger.error(f"Generated directory not found: {GENERATED_DIR}")

@app.get("/")
async def serve_frontend():
    """Serve frontend HTML file."""
    if FRONTEND_INDEX.exists():
        try:
            html_content = FRONTEND_INDEX.read_text(encoding="utf-8")
            return HTMLResponse(content=html_content)
        except Exception as e:
            logger.error(f"Error reading frontend file: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to read frontend file."
            )
    else:
        logger.error(f"Frontend index file not found: {FRONTEND_INDEX}")
        return HTMLResponse(
            content="<h1>Frontend not found</h1><p>Please ensure frontend/index.html exists.</p>",
            status_code=404
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "generator_initialized": generator is not None,
        "api_key_configured": bool(os.getenv('GROQ_API_KEY'))
    }

@app.post("/generate", response_model=GenerateResponse)
async def generate_website(request: GenerateRequest):
    """Generate a website from the given prompt."""
    # Validate generator is available
    if not generator:
        logger.error("Generation attempted but generator not initialized")
        raise HTTPException(
            status_code=503,
            detail="Website generator not initialized. Check API key configuration."
        )
    
    # Validate request data
    if not request.prompt or not request.prompt.strip():
        logger.warning("Empty prompt received")
        raise HTTPException(
            status_code=400,
            detail="Prompt cannot be empty"
        )
    
    if len(request.prompt) > 1000:
        logger.warning(f"Prompt too long: {len(request.prompt)} characters")
        raise HTTPException(
            status_code=400,
            detail="Prompt too long (max 1000 characters)"
        )
    
    try:
        logger.info(f"Generating website for prompt: {request.prompt[:100]}...")
        result = generator.generate_website(request.prompt)
        
        if result["success"]:
            logger.info(f"Website generated successfully: {result.get('project_name')}")
            return GenerateResponse(**result)
        else:
            error_msg = result.get('error', 'Unknown generation error')
            error_type = result.get('error_type', 'Unknown')
            logger.error(f"Website generation failed: {error_type} - {error_msg}")
            return GenerateResponse(**result)
            
    except Exception as e:
        logger.error(f"Unexpected error during generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during generation: {str(e)}"
        )

@app.get("/project/info", response_model=ProjectInfo)
async def get_project_info():
    """Get information about the current project."""
    if not generator:
        logger.error("Project info requested but generator not initialized")
        raise HTTPException(
            status_code=503,
            detail="Website generator not initialized."
        )
    
    try:
        info = generator.get_project_info()
        logger.info(f"Project info retrieved: {info['total_files']} files")
        return ProjectInfo(**info)
    except Exception as e:
        logger.error(f"Error getting project info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get project info: {str(e)}"
        )

@app.delete("/project/clean")
async def clean_project():
    """Clean all generated files."""
    if not generator:
        logger.error("Project clean requested but generator not initialized")
        raise HTTPException(
            status_code=503,
            detail="Website generator not initialized."
        )
    
    try:
        success = generator.clean_project()
        if success:
            logger.info("Project cleaned successfully")
            return {"success": True, "message": "Project cleaned successfully"}
        else:
            logger.warning("Project clean operation failed")
            return {"success": False, "message": "Failed to clean project"}
    except Exception as e:
        logger.error(f"Error cleaning project: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clean project: {str(e)}"
        )

@app.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """Download a generated file."""
    if not generator:
        raise HTTPException(
            status_code=503,
            detail="Website generator not initialized."
        )
    
    try:
        # Security check - ensure file is within project root
        project_root = generator.project_root
        file_full_path = project_root / file_path
        
        # Resolve paths to prevent directory traversal
        file_full_path = file_full_path.resolve()
        project_root = project_root.resolve()
        
        if not str(file_full_path).startswith(str(project_root)):
            logger.warning(f"Directory traversal attempt: {file_path}")
            raise HTTPException(status_code=403, detail="Access denied - path outside project root")
        
        if not file_full_path.exists():
            logger.warning(f"File not found: {file_full_path}")
            raise HTTPException(status_code=404, detail="File not found")
        
        # Determine media type based on file extension
        media_type = 'application/octet-stream'
        if file_full_path.suffix.lower() == '.html':
            media_type = 'text/html'
        elif file_full_path.suffix.lower() == '.css':
            media_type = 'text/css'
        elif file_full_path.suffix.lower() == '.js':
            media_type = 'application/javascript'
        
        logger.info(f"Serving file: {file_path} ({media_type})")
        
        return FileResponse(
            path=file_full_path,
            filename=file_full_path.name,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {file_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

@app.get("/download-zip")
async def download_project_zip():
    """Download the entire generated project as a ZIP file."""
    if not generator:
        logger.error("ZIP download attempted but generator not initialized")
        raise HTTPException(
            status_code=503,
            detail="Website generator not initialized."
        )
    
    try:
        project_root = generator.project_root
        
        # Check if project directory exists and has files
        if not project_root.exists():
            logger.warning(f"Project directory not found: {project_root}")
            raise HTTPException(
                status_code=404,
                detail="No generated project found."
            )
        
        # Get all files in the project directory
        files = list(project_root.rglob("*"))
        files = [f for f in files if f.is_file()]
        
        if not files:
            logger.warning("Project directory is empty")
            raise HTTPException(
                status_code=404,
                detail="Generated project is empty."
            )
        
        logger.info(f"Creating ZIP with {len(files)} files from {project_root}")
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in files:
                # Calculate relative path from project root
                relative_path = file_path.relative_to(project_root)
                
                # Add file to ZIP with proper path structure
                zip_file.write(file_path, str(relative_path))
                logger.debug(f"Added to ZIP: {relative_path}")
        
        zip_buffer.seek(0)
        zip_data = zip_buffer.getvalue()
        
        # Get project name for filename
        project_info = generator.get_project_info()
        project_name = project_info.get('project_name', 'website')
        if not project_name or project_name.strip() == '':
            project_name = 'website'
        
        # Sanitize project name for filename
        safe_project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        zip_filename = f"{safe_project_name}.zip"
        
        logger.info(f"Created ZIP: {zip_filename} ({len(zip_data)} bytes)")
        
        # Return ZIP file as response
        from fastapi.responses import Response
        return Response(
            content=zip_data,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}",
                "Content-Length": str(len(zip_data))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ZIP download: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create ZIP file: {str(e)}"
        )

@app.get("/api/info")
async def api_info():
    """API information endpoint."""
    return {
        "message": "CoderBuddy AI Website Generator API",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "generate": "/generate",
            "project_info": "/project/info",
            "api_docs": "/docs"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
