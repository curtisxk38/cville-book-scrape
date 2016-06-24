import requests
from lxml import html

class CatalogItem():
	def __init__(self, title, link, details, availability, copies, origin):
		self.title = title
		self.link = link
		self.details = details
		self.availability = availability
		self.copies_text = copies
		self.origin = origin

	def __str__(self):
		return "{}\n{}\n{}".format(self.title, self.copies_text, self.availability)

def format_jmrl_details(div):
	details = div.xpath("text()")
	formatted = ""
	for i in details:
		i = i.strip()
		if i:
			formatted += i + " "
	return formatted.strip()

def jmrl(search_type, search_field):
	payload = (("searchtype", search_type), ("searcharg", search_field))
	get_source = "http://aries.jmrl.org/search/"
	
	r = requests.get(get_source, params=payload)
	tree = html.fromstring(r.content)

	items = []

	title = tree.xpath("//h2[@class='briefcitTitle']/a/text()")
	link = ["http://aries.jmrl.org" + i for i in tree.xpath("//h2[@class='briefcitTitle']/a/@href")]
	copies = [i.strip() for i in tree.xpath("//div[@class='briefcitItemsMain']/text()")]
	detail_divs = tree.xpath("//div[@class='briefcitDetailMain']")
	
	more_links = tree.xpath("//td[@class='browsePager']/a/@href")

	availability = [i != "Currently no copies available" for i in copies]

	if len(title) == len(link) == len(copies) == len(detail_divs):
		for i in range(len(title)):
			c = CatalogItem(title[i], link[i], format_jmrl_details(detail_divs[i]), availability[i], copies[i], "JMRL")
			items.append(c)
	
	return items, ["http://aries.jmrl.org" + i for i in more_links]


def format_virgo_details(dd):
	elements = dd.xpath("./*/text()")
	formatted = ""
	if "Availability" in elements:
		elements.remove("Availability")
	for index, e in enumerate(elements):
		if e.strip():
			formatted += e.strip()
			if index % 2 == 0:
				formatted += ": "
			else:
				formatted += "\n"
	return formatted.strip()

def virgo_availability(link):
	link = link.replace("details", "brief_availability")
	r = requests.get(link)
	tree = html.fromstring(r.content)
	strings = [i.strip() for i in tree.xpath("//span/text()")]
	if len(strings) < 3:
		return True, "View Online"
	return strings[0] == "Available", "{} ({})".format(strings[2], strings[4])

def virgo(search_type, search_field):
	if search_type == "t":
		search_type = "title"
	if search_type == "a":
		search_type = "author"
	payload = ((search_type, search_field), ("sort_key", "relevancy"), ("search_field", "advanced"))
	get_source = "http://search.lib.virginia.edu/catalog"

	r = requests.get(get_source, params=payload)
	tree = html.fromstring(r.content)
	
	items = []
	title = tree.xpath("//dd[@class='titleField']/descendant::a/text()")
	link = ["http://search.lib.virginia.edu" + i for i in tree.xpath("//dd[@class='titleField']/descendant::a/@href")]
	details = tree.xpath("//div[@class='details']/dl[@class='metadata']")

	copies = []
	availability = []
	
	for li in link:
		a, c = virgo_availability(li)
		availability.append(a)
		copies.append(c)

	more_links = tree.xpath("//nav[@class='pagination']/span/a/@href")

	if len(title) == len(link) == len(details): # == len(copies)
		for i in range(len(title)):
			c = CatalogItem(title[i], link[i], format_virgo_details(details[i]), availability[i], copies[i], "UVa")
			items.append(c)

	return items, ["http://search.lib.virginia.edu" + i for i in more_links]


if __name__ == "__main__":
	items = []
	it, l = virgo("t", "do androids")
	items.extend(it)

	for i in items:
		print(i)