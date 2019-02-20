from django.template import Library
import markdown
from markdown.extensions import Extension

# https://github.com/Python-Markdown/markdown/commit/7db56daedf8a6006222f55eeeab748e7789fba89 
# per notes in the release docs for version 2.5, used an EscapeHTML 
# extension to replace safe_mode=”escape” (deprecated)

class EscapeHtml(Extension):
	def extendMarkdown(self, md, md_globals):
		del md.preprocessors['html_block']
		del md.inlinePatterns['html']

register = Library()

@register.filter
def markdownify(text):
    return markdown.markdown(text,extensions=[EscapeHtml()])