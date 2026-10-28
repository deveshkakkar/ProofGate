#!/usr/bin/env python3
"""Approved readonly-auth mount + read-only candidate + no model command tools."""
import os,sys
ROOT='/workspace/scratch/95589aefb3bf/proofgate'
# Preserve mandatory sandbox/network transport configuration, never API credentials
# or remote-executor endpoints. App-server reads existing approved auth mount.
allow={'PATH','LANG','LC_ALL','TERM','HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY','http_proxy','https_proxy','all_proxy','no_proxy','WS_PROXY','WSS_PROXY','ws_proxy','wss_proxy','SSL_CERT_FILE','SSL_CERT_DIR','NODE_EXTRA_CA_CERTS','NODE_USE_ENV_PROXY','CODEX_PERMISSION_PROFILE','CODEX_SANDBOX_NETWORK_DISABLED','CODEX_NETWORK_PROXY_ACTIVE','CODEX_PROXY_CERT','CODEX_NETWORK_ALLOW_LOCAL_BINDING'}
env={k:v for k,v in os.environ.items() if k in allow}
args=['bwrap','--unshare-user','--unshare-pid','--unshare-ipc','--unshare-uts','--new-session','--die-with-parent','--cap-drop','ALL','--ro-bind','/','/','--tmpfs','/tmp','--tmpfs','/run','--proc','/proc','--dev','/dev','--ro-bind',ROOT+'/candidate',ROOT+'/candidate','--bind',ROOT+'/supervisor/codex-runtime','/tmp/codex-home','--ro-bind','/home/agent/.codex/auth.json','/tmp/codex-home/auth.json','--ro-bind','/home/agent/.codex/config.toml','/tmp/codex-home/config.toml','--tmpfs','/home/agent','--setenv','CODEX_HOME','/tmp/codex-home','--setenv','HOME','/tmp','--setenv','PATH',ROOT+'/toolchains/lean-4.34.0-linux/bin:'+ROOT+'/toolchains/bend/bin:'+env.get('PATH','/usr/bin:/bin'),'--setenv','BENDTT',ROOT+'/toolchains/home/.bend/bendtt/e951a3ff12c837f2/bendtt','--setenv','BEND_NO_TELEMETRY','1','--chdir',ROOT+'/candidate','/opt/codex/bin/codex','exec','--json','-s','read-only']
settings=['project_doc_max_bytes=0','features.shell_tool=false','features.unified_exec=false','features.apply_patch_freeform=false','features.code_mode=false','features.browser_use=false','features.shell_snapshot=false','features.skip_host_skill_discovery=true','features.apps=false','features.plugins=false','features.remote_plugin=false','features.image_generation=false','features.tool_search=false','apps._default.enabled=false']
for s in settings:args+=['-c',s]
args+=sys.argv[1:]
os.execvpe('bwrap',args,env)
