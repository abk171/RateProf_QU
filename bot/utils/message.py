from datetime import datetime, timezone
from urllib.parse import urlparse


def age_check(msg):
    age = (datetime.now(timezone.utc) - msg.created_at).total_seconds()
    if age >= 1209600:
        return False
    return True


def cleanup_code(content):
    """Automatically removes code blocks from the code."""
    # remove ```py\n```
    if content.startswith('```') and content.endswith('```'):
        return '\n'.join(content.split('\n')[1:-1])

    # remove `foo`
    return content.strip('` \n')


emojis = {'A': '🇦', 'B': '🇧', 'C': '🇨', 'D': '🇩', 'E': '🇪', 'F': '🇫', 'G': '🇬', 'H': '🇭', 'I': '🇮', 'J': '🇯', 'K': '🇰', 'L': '🇱', 'M': '🇲',
          'N': '🇳', 'O': '🇴', 'P': '🇵', 'Q': '🇶', 'R': '🇷', 'S': '🇸', 'T': '🇹', 'U': '🇺', 'V': '🇻', 'W': '🇼', 'X': '🇽', 'Y': '🇾', 'Z': '🇿', ' ': '  ', '!': '❗', '?': '❓',
          '0': '0\N{variation selector-16}\N{combining enclosing keycap}',
          '1': '1\N{variation selector-16}\N{combining enclosing keycap}',
          '2': '2\N{variation selector-16}\N{combining enclosing keycap}',
          '3': '3\N{variation selector-16}\N{combining enclosing keycap}',
          '4': '4\N{variation selector-16}\N{combining enclosing keycap}',
          '5': '5\N{variation selector-16}\N{combining enclosing keycap}',
          '6': '6\N{variation selector-16}\N{combining enclosing keycap}',
          '7': '7\N{variation selector-16}\N{combining enclosing keycap}',
          '8': '8\N{variation selector-16}\N{combining enclosing keycap}',
          '9': '9\N{variation selector-16}\N{combining enclosing keycap}',
          '10': '🔟'}

checkmark_emoji = '<:checkmark:746740742818365441>'
crossmark_emoji = '<:crossmark:746740790688219188>'
