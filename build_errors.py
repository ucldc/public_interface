# builds django error pages
# if no command line arguments are given looks for the UCLDC_GA_SITE_CODE env variable
# otherwise uses first command line argument

import sys
from jinja2 import Environment, PackageLoader, select_autoescape
from public_interface.settings import GA_SITE_CODE

gaSiteCode = GA_SITE_CODE

if (len(sys.argv) == 3 and sys.argv[1] == "--ga-site-code"):
	gaSiteCode = sys.argv[2]
elif (len(sys.argv) != 1):
	print('python build_errors.py --ga-site-code <site code>')


env = Environment(loader = PackageLoader('calisphere', 'templates/error_templates'), 
				  autoescape=select_autoescape(['html', 'xml']))

template_files = env.list_templates()

for file in template_files:
	template = env.get_template(file)
	with open(f"calisphere/templates/{file}", "w") as fh:
		fh.write(template.render(gaSiteCode=gaSiteCode))