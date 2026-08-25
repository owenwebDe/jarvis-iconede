servers_yaml = """
    # Re-added servers
    demo-builder:
      command: "python"
      args: ["tools/demo_builder_server.py"]
      env:
        PYTHONUNBUFFERED: "1"

    predictive-proactivity:
      command: "python"
      args: ["tools/predictive_proactivity_server.py"]
      env:
        PYTHONUNBUFFERED: "1"

    workflow-templates:
      command: "python"
      args: ["tools/workflow_templates_server.py"]
      env:
        PYTHONUNBUFFERED: "1"

    voice-briefing:
      command: "python"
      args: ["tools/voice_briefing_server.py"]
      env:
        PYTHONUNBUFFERED: "1"

    business-intel:
      command: "python"
      args: ["tools/business_intel_server.py"]
      env:
        PYTHONUNBUFFERED: "1"

    multi-user-rbac:
      command: "python"
      args: ["tools/multi_user_rbac_server.py"]
      env:
        PYTHONUNBUFFERED: "1"

    comm-hub:
      command: "python"
      args: ["tools/comm_hub_server.py"]
      env:
        PYTHONUNBUFFERED: "1"

    knowledge-base:
      command: "python"
      args: ["tools/knowledge_base_server.py"]
      env:
        PYTHONUNBUFFERED: "1"

    client-portal:
      command: "python"
      args: ["tools/client_portal_server.py"]
      env:
        PYTHONUNBUFFERED: "1"

    predictive-forecast:
      command: "python"
      args: ["tools/predictive_forecast_server.py"]
      env:
        PYTHONUNBUFFERED: "1"

    advanced-workflow:
      command: "python"
      args: ["tools/advanced_workflow_server.py"]
      env:
        PYTHONUNBUFFERED: "1"

    performance-cache:
      command: "python"
      args: ["tools/performance_cache_server.py"]
      env:
        PYTHONUNBUFFERED: "1"

    advanced-analytics:
      command: "python"
      args: ["tools/advanced_analytics_server.py"]
      env:
        PYTHONUNBUFFERED: "1"

    calendar-task:
      command: "python"
      args: ["tools/calendar_task_server.py"]
      env:
        PYTHONUNBUFFERED: "1"

    music-playlist:
      command: "python"
      args: ["tools/music_playlist_server.py"]
      env:
        PYTHONUNBUFFERED: "1"

    social-media:
      command: "python"
      args: ["tools/social_media_server.py"]
      env:
        PYTHONUNBUFFERED: "1"

    seo-optimizer:
      command: "python"
      args: ["tools/seo_optimizer_server.py"]
      env:
        PYTHONUNBUFFERED: "1"
"""

with open("fastagent.config.yaml", "a", encoding="utf-8") as f:
    f.write(servers_yaml)

print("Servers successfully appended to fastagent.config.yaml")
