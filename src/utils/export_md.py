import re
import glob
from .tracing import logger

def export_to_markdown(srs_content: str) -> str:
  """
  Export SRS to markdown file with auto versioning (short filename)
  """
  existing_files = glob.glob("SRS_version_*.md")

  # Get the current largest version
  max_ver = 0
  for file in existing_files:
    match = re.search(r"SRS_version_(\d+)\.md", file)
    if match:
      max_ver = max(max_ver, int(match.group(1)))
      
  # Next version
  next_ver = max_ver + 1
  filename = f"SRS_version_{next_ver}.md"

  with open(filename, "w", encoding="utf-8") as f:
    f.write(srs_content)

  logger.log("EXPORT_SUCCESS", f"SRS exported to {filename}", level="SUCCESS")
  print(f"\nSRS Document exported to: {filename}")

  return filename