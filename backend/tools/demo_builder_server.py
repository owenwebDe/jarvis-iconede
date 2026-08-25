"""Demo Builder FastMCP Server.

Enables DemoBuilderAgent and Jarvis to generate modern, high-converting
client demo websites across ANY industry (Real Estate, Restaurants, Boutiques, Clinics)
in seconds and deploy them to live Vercel URLs.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP

_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from services.demo_generator import get_demo_generator
from services.vercel_deployer import get_vercel_deployer

logger = logging.getLogger("demo_builder_server")
mcp = FastMCP("DemoBuilder")


@mcp.tool()
def demo_build_website(
    business_name: str,
    industry: str = "auto",
    location: str = "Abuja, Nigeria",
    phone_number: str = "+234 800 000 0000",
    tagline: str = "",
    theme: str = "light",
    auto_deploy: bool = True,
) -> str:
    """Universal website generator for ANY industry (Portfolio, Real Estate, SaaS, Clinics, Restaurants).

    Automatically crafts a high-fashion, mobile-first, zero-emoji interactive web app
    and deploys it directly to a live production cloud URL on Vercel.

    Args:
        business_name: Name of the brand or person (e.g. 'Owen', 'Ordanic Homes', 'Kitchen Glory').
        industry: 'portfolio' | 'real_estate' | 'restaurant' | 'clinic' | 'fashion' | 'saas' | 'auto'.
        location: City/district (e.g. 'Abuja, Nigeria' or 'Maitama, Abuja').
        phone_number: Contact phone or WhatsApp number.
        tagline: Slogan, value proposition, or specialty.
        theme: 'light' or 'dark'.
        auto_deploy: Automatically deploy to live Vercel URL (defaults to True).
    """
    # Smart Parameter Resolution
    clean_name = business_name.strip()
    if clean_name.lower() in ("your name", "my portfolio", "me", "myself", "portfolio", "owner", "admin"):
        clean_name = "Owen"
        if not tagline or "tagline" in tagline.lower():
            tagline = "Executive Full-Stack AI Engineer & Creative Technologist"
        if not location or "location" in location.lower():
            location = "Abuja, Nigeria"
        if industry == "auto":
            industry = "portfolio"

    generator = get_demo_generator()
    meta = generator.generate_website_demo(
        business_name=clean_name,
        industry=industry,
        location=location,
        phone_number=phone_number,
        tagline=tagline,
        default_theme=theme,
    )
    
    deployment_url = None
    if auto_deploy:
        try:
            deployer = get_vercel_deployer()
            d_res = deployer.deploy_directory(meta["directory"], project_name=meta["demo_id"])
            deployment_url = d_res.get("deployment_url")
        except Exception as e:
            logger.warning(f"Auto-deployment failed: {e}")

    return json.dumps({
        "status": "success",
        "demo_id": meta["demo_id"],
        "business_name": clean_name,
        "category": meta.get("category", industry),
        "location": location,
        "deployment_url": deployment_url,
        "entrypoint": meta["entrypoint"],
        "directory": meta["directory"],
        "message": f"Successfully generated and deployed ultra-luxury demo for {clean_name} at {deployment_url or meta['entrypoint']}",
    }, indent=2)


@mcp.tool()
def demo_build_real_estate_website(
    business_name: str = "Ordanic Homes",
    location: str = "Maitama, Guzape & Jabi, Abuja",
    phone_number: str = "+234 814 000 7788",
    tagline: str = "Curating architectural marvels, luxury villas & premium real estate investments in Abuja.",
    theme: str = "light",
    auto_deploy: bool = True,
) -> str:
    """Generate an ultra-modern luxury Real Estate & Property Development web app (Prospera Kit).

    Includes penthouse & villa showcases, price tags (in Millions/Billions), floor plans,
    specs (beds/baths/sqm), private inspection booking modal, and WhatsApp consultation.
    Automatically deploys to live Vercel cloud URL.
    """
    generator = get_demo_generator()
    meta = generator.generate_real_estate_demo(
        business_name=business_name,
        location=location,
        phone_number=phone_number,
        tagline=tagline,
        default_theme=theme,
    )
    deployment_url = None
    if auto_deploy:
        try:
            deployer = get_vercel_deployer()
            d_res = deployer.deploy_directory(meta["directory"], project_name=meta["demo_id"])
            deployment_url = d_res.get("deployment_url")
        except Exception as e:
            logger.warning(f"Auto-deployment failed: {e}")

    return json.dumps({
        "status": "success",
        "demo_id": meta["demo_id"],
        "business_name": business_name,
        "category": "real_estate",
        "location": location,
        "deployment_url": deployment_url,
        "entrypoint": meta["entrypoint"],
        "directory": meta["directory"],
        "message": f"Successfully generated and deployed real estate demo for {business_name} at {deployment_url or meta['directory']}",
    }, indent=2)


@mcp.tool()
def demo_build_luxoria_real_estate_website(
    business_name: str = "Ordanic Homes",
    location: str = "Maitama, Guzape & Jabi, Abuja",
    phone_number: str = "+234 814 000 7788",
    tagline: str = "Architectural marvels for connoisseurs of distinction across Abuja.",
    theme: str = "light",
    auto_deploy: bool = True,
) -> str:
    """Generate an ultra-exclusive Luxoria-grade luxury Real Estate web application.

    Based on the world-renowned Luxoria Elementor master kit: features architectural hero layout,
    bronze-gold luxury accents, live stats counters, district filter tabs, villa modal floor plans,
    confidential private tour scheduling, and WhatsApp concierge integration.
    Automatically deploys to live Vercel cloud URL.
    """
    generator = get_demo_generator()
    meta = generator.generate_luxoria_demo(
        business_name=business_name,
        location=location,
        phone_number=phone_number,
        tagline=tagline,
        default_theme=theme,
    )
    deployment_url = None
    if auto_deploy:
        try:
            deployer = get_vercel_deployer()
            d_res = deployer.deploy_directory(meta["directory"], project_name=meta["demo_id"])
            deployment_url = d_res.get("deployment_url")
        except Exception as e:
            logger.warning(f"Auto-deployment failed: {e}")

    return json.dumps({
        "status": "success",
        "demo_id": meta["demo_id"],
        "business_name": business_name,
        "category": "luxoria_real_estate",
        "location": location,
        "deployment_url": deployment_url,
        "entrypoint": meta["entrypoint"],
        "directory": meta["directory"],
        "message": f"Successfully generated and deployed Luxoria real estate demo for {business_name} at {deployment_url or meta['directory']}",
    }, indent=2)


@mcp.tool()
def demo_build_restaurant_website(
    business_name: str,
    location: str = "Wuse 2, Abuja",
    phone_number: str = "+234 800 000 0000",
    tagline: str = "Exquisite Dining & Fast Online Ordering",
    theme: str = "light",
    auto_deploy: bool = True,
) -> str:
    """Generate an ultra-modern, luxury restaurant web app for a prospect.

    Includes digital menu, category tabs, cart drawer, VIP table booking, and WhatsApp checkout.
    Automatically deploys to live Vercel cloud URL.
    """
    generator = get_demo_generator()
    meta = generator.generate_restaurant_demo(
        business_name=business_name,
        location=location,
        phone_number=phone_number,
        tagline=tagline,
        default_theme=theme,
    )
    deployment_url = None
    if auto_deploy:
        try:
            deployer = get_vercel_deployer()
            d_res = deployer.deploy_directory(meta["directory"], project_name=meta["demo_id"])
            deployment_url = d_res.get("deployment_url")
        except Exception as e:
            logger.warning(f"Auto-deployment failed: {e}")

    return json.dumps({
        "status": "success",
        "demo_id": meta["demo_id"],
        "business_name": business_name,
        "category": "restaurant",
        "location": location,
        "deployment_url": deployment_url,
        "entrypoint": meta["entrypoint"],
        "directory": meta["directory"],
        "message": f"Successfully generated and deployed restaurant demo for {business_name} at {deployment_url or meta['directory']}",
    }, indent=2)


@mcp.tool()
def demo_build_portfolio_website(
    business_name: str = "Owen",
    location: str = "Abuja, Nigeria",
    phone_number: str = "+234 800 000 0000",
    tagline: str = "Executive Full-Stack AI Engineer & Creative Technologist",
    theme: str = "dark",
    auto_deploy: bool = True,
) -> str:
    """Generate an executive, award-winning Portfolio & Personal Brand web application.

    Features status ticker, glassmorphic navbar, hero with trust metrics, live stats counter bar,
    curated project showcase, full-stack capabilities matrix, and direct WhatsApp concierge booking.
    Automatically deploys to live Vercel cloud URL.
    """
    clean_name = business_name.strip()
    if clean_name.lower() in ("your name", "my portfolio", "me", "myself", "portfolio", "owner", "admin"):
        clean_name = "Owen"
        if not tagline or "tagline" in tagline.lower():
            tagline = "Executive Full-Stack AI Engineer & Creative Technologist"

    generator = get_demo_generator()
    meta = generator.generate_portfolio_demo(
        business_name=clean_name,
        location=location,
        phone_number=phone_number,
        tagline=tagline,
        default_theme=theme,
    )
    deployment_url = None
    if auto_deploy:
        try:
            deployer = get_vercel_deployer()
            d_res = deployer.deploy_directory(meta["directory"], project_name=meta["demo_id"])
            deployment_url = d_res.get("deployment_url")
        except Exception as e:
            logger.warning(f"Auto-deployment failed: {e}")

    return json.dumps({
        "status": "success",
        "demo_id": meta["demo_id"],
        "business_name": clean_name,
        "category": "portfolio",
        "location": location,
        "deployment_url": deployment_url,
        "entrypoint": meta["entrypoint"],
        "directory": meta["directory"],
        "message": f"Successfully generated and deployed executive portfolio demo for {clean_name} at {deployment_url or meta['directory']}",
    }, indent=2)


@mcp.tool()
def demo_deploy_to_cloud(demo_id: str, project_name: str = "") -> str:
    """Deploy a generated demo website to Vercel and return a live public URL.

    Args:
        demo_id: The ID of the demo generated by demo_build_website / demo_build_real_estate_website / demo_build_restaurant_website.
        project_name: Optional custom project slug (e.g. 'ordanic-homes-demo').
    """
    demos_dir = _BACKEND_DIR / "data" / "demos" / demo_id
    if not demos_dir.exists():
        demos_dir = _BACKEND_DIR / "data" / "react_projects" / demo_id
    if not demos_dir.exists():
        return json.dumps({
            "status": "error",
            "message": f"Demo directory for ID '{demo_id}' not found.",
        })

    deployer = get_vercel_deployer()
    name = project_name or demo_id
    res = deployer.deploy_directory(demos_dir, project_name=name)
    return json.dumps(res, indent=2)


@mcp.tool()
def demo_create_react_project(
    business_name: str,
    industry: str = "real_estate",
    archetype: str = "auto",
    mode: str = "marketing",
    location: str = "Abuja, Nigeria",
    phone_number: str = "+234 800 000 0000",
    tagline: str = "",
    theme: str = "dark",
    auto_deploy: bool = True,
) -> str:
    """Create a modular React + TypeScript + Vite project with Design Intelligence & Git versioning.

    Supports Multi-Archetypes: 'luxury', 'tech_saas', 'minimal_editorial', 'hospitality_dining', 'corporate_legal'.

    Args:
        business_name: Name of the business or client (e.g. 'Ordanic Homes', 'Owen').
        industry: Industry category (e.g. 'real_estate', 'portfolio', 'restaurant', 'saas').
        archetype: Design archetype ('luxury', 'tech_saas', 'minimal_editorial', 'hospitality_dining', 'corporate_legal', or 'auto').
        mode: 'marketing' (landing/showcase) or 'application' (dashboard/SaaS).
        location: City/neighborhood.
        phone_number: Contact WhatsApp/phone.
        tagline: Primary value proposition.
        theme: 'dark' or 'light'.
        auto_deploy: Automatically deploy to live Vercel cloud URL (default True).
    """
    from services.react_project_service import get_react_project_service
    service = get_react_project_service()
    meta = service.create_project(
        business_name=business_name,
        industry=industry,
        archetype=archetype,
        mode=mode,
        location=location,
        phone_number=phone_number,
        tagline=tagline,
        theme=theme,
    )
    
    deployment_url = None
    if auto_deploy:
        try:
            d_res = service.deploy_project(meta["project_id"])
            deployment_url = d_res.get("deployment_url")
        except Exception as e:
            logger.warning(f"Auto-deployment failed for React project: {e}")

    return json.dumps({
        "status": "success",
        "project_id": meta["project_id"],
        "business_name": business_name,
        "archetype": meta.get("archetype"),
        "mode": mode,
        "location": location,
        "deployment_url": deployment_url,
        "entrypoint": meta["entrypoint"],
        "directory": meta["directory"],
        "message": f"Successfully created modular React project for {business_name} at {deployment_url or meta['directory']}",
    }, indent=2)


@mcp.tool()
def demo_patch_component(
    project_id: str,
    file_path: str,
    target_content: str,
    replacement_content: str,
    preferred_layer: int = 1,
    auto_deploy: bool = False,
) -> str:
    """Surgically edit a specific React component using layered precision editing and Git checkpointing.

    Target only the exact lines/JSX you need to update (e.g. in 'src/components/Hero.tsx').

    Args:
        project_id: ID of the React project (e.g. 'ordanic-homes-3ea4ad').
        file_path: Relative path to the file (e.g. 'src/components/Hero.tsx').
        target_content: Exact substring to replace.
        replacement_content: New content to insert.
        preferred_layer: 1 (exact substring), 2 (trimmed line), 3 (regex token).
        auto_deploy: Automatically deploy updated build to Vercel (default False).
    """
    from services.react_project_service import get_react_project_service
    service = get_react_project_service()
    res = service.patch_component(
        project_id=project_id,
        rel_path=file_path,
        target_content=target_content,
        replacement_content=replacement_content,
        preferred_layer=preferred_layer,
    )
    if res.get("status") == "success" and auto_deploy:
        try:
            d_res = service.deploy_project(project_id)
            res["deployment_url"] = d_res.get("deployment_url")
        except Exception as e:
            logger.warning(f"Auto-deploy failed on component patch: {e}")

    return json.dumps(res, indent=2)


@mcp.tool()
def demo_write_component(
    project_id: str,
    file_path: str,
    code: str,
    auto_deploy: bool = False,
) -> str:
    """Write or overwrite a single focused React component (e.g. 'src/components/Pricing.tsx').

    Args:
        project_id: ID of the React project.
        file_path: Relative path to file (e.g. 'src/components/Hero.tsx').
        code: Full code of the component.
        auto_deploy: Automatically deploy to Vercel (default False).
    """
    from services.react_project_service import get_react_project_service
    service = get_react_project_service()
    res = service.write_component(project_id=project_id, rel_path=file_path, code=code)
    if res.get("status") == "success" and auto_deploy:
        try:
            d_res = service.deploy_project(project_id)
            res["deployment_url"] = d_res.get("deployment_url")
        except Exception as e:
            logger.warning(f"Auto-deploy failed on component write: {e}")

    return json.dumps(res, indent=2)


@mcp.tool()
def demo_rollback_project(project_id: str, target: str = "HEAD~1") -> str:
    """Roll back project to previous Git checkpoint if QA or Critic detects regression.

    Args:
        project_id: ID of the React project.
        target: Git checkpoint ref (default 'HEAD~1').
    """
    from services.react_project_service import get_react_project_service
    service = get_react_project_service()
    res = service.rollback_project(project_id=project_id, target=target)
    return json.dumps(res, indent=2)


@mcp.tool()
def demo_get_project_tree(project_id: str) -> str:
    """Inspect the component and file tree of a modular React project.

    Args:
        project_id: ID of the React project.
    """
    from services.react_project_service import get_react_project_service
    service = get_react_project_service()
    res = service.get_project_tree(project_id)
    return json.dumps(res, indent=2)


@mcp.tool()
def demo_read_component(project_id: str, file_path: str) -> str:
    """Read the source code of a specific component before performing surgical edits.

    Args:
        project_id: ID of the React project.
        file_path: Relative path to file (e.g. 'src/components/Hero.tsx').
    """
    from services.react_project_service import get_react_project_service
    service = get_react_project_service()
    res = service.read_component(project_id=project_id, rel_path=file_path)
    return json.dumps(res, indent=2)


@mcp.tool()
def demo_get_project_manifest(project_id: str) -> str:
    """Retrieve full .jarvis/ project manifest (design, routes, components, business, assets).

    Args:
        project_id: ID of the project (e.g. 'ordanic-homes-a9c299').
    """
    from services.react_project_service import get_react_project_service
    service = get_react_project_service()
    res = service.get_manifest(project_id)
    return json.dumps(res, indent=2)


@mcp.tool()
def demo_browser_test(
    project_id: str,
    routes: list[str] = [],
    viewports: list[str] = ["desktop", "mobile"],
) -> str:
    """Run Playwright automated browser test (console errors, overflow, responsive, screenshots).

    Gating test: verifies 0 console errors and 0 layout overflow before cloud deployment.

    Args:
        project_id: ID of the React project.
        routes: List of routes to test (e.g. ['/']).
        viewports: Viewports to test (['desktop', 'mobile']).
    """
    from services.react_project_service import get_react_project_service
    service = get_react_project_service()
    res = service.run_browser_qa(project_id=project_id, routes=routes, viewports=viewports)
    return json.dumps(res, indent=2)


@mcp.tool()
def demo_visual_analyze(
    project_id: str,
    routes: list[str] = [],
    viewports: list[str] = ["desktop", "mobile"],
    compare_to_design_spec: bool = True,
    requirements: str = "",
) -> str:
    """Execute Quantitative Visual Critic: 10-Point Rubric + AI Anti-Pattern detector + Spec comparison.

    Evaluates Layout, Typography, Spacing, Color Consistency, Hierarchy, Imagery, Mobile UX, and Animations.

    Args:
        project_id: ID of the React project.
        routes: List of routes.
        viewports: Viewports to inspect.
        compare_to_design_spec: Compare against .jarvis/design.json (default True).
        requirements: Original client requirements prompt for ground-truth comparison.
    """
    from services.react_project_service import get_react_project_service
    service = get_react_project_service()
    res = service.run_visual_critic(
        project_id=project_id,
        routes=routes,
        viewports=viewports,
        compare_to_design_spec=compare_to_design_spec,
        requirements=requirements,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def demo_build(project_id: str) -> str:
    """Compile a React/Vite project into production static distribution bundle.

    Args:
        project_id: ID of the project.
    """
    from services.react_project_service import get_react_project_service
    service = get_react_project_service()
    res = service.build_project(project_id)
    return json.dumps(res, indent=2)


@mcp.tool()
def demo_deploy(project_id: str) -> str:
    """Deploy compiled project to Vercel production and return live public URL.

    Args:
        project_id: ID of the project.
    """
    from services.react_project_service import get_react_project_service
    service = get_react_project_service()
    res = service.deploy_project(project_id)
    return json.dumps(res, indent=2)


if __name__ == "__main__":
    mcp.run()



