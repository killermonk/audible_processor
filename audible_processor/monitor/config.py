from dataclasses import dataclass

@dataclass
class DaemonConfig:
    """Class holding the config for the daemon"""
    activation_bytes: str
    output_dir: str
    create_author_dir: bool
    create_title_dir: bool
