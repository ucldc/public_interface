// references bug https://www.pivotaltracker.com/story/show/151812193
// where after a user downloads an image and navigates back to search results
// the search results page has lost context despite initally looking the same
// (can't paginate forward, X out search within pill)

module.exports = async (page, scenario, vp) => {
	console.log('SCENARIO > ' + scenario.label);
	await require('./clickAndHoverHelper')(page, scenario);

	// add more ready handlers here...
	let searchWithinElementHandle = await page.$('#search-collection__field');
	await searchWithinElementHandle.type('doctor');

	// search UCSF items for 'doctor' & get number of results found
	let searchForDoctor = await Promise.all([
		page.waitForResponse(response => response.status() === 200),
		searchWithinElementHandle.press('Enter'),
  	]);
  	let resultsFound = await page.$eval('h3.text__collections-heading', el => el.innerText);

  	// click into the first item
  	let navigateToFirstItem = await Promise.all([
		page.waitForNavigation(),
		page.waitFor(1000),
		page.click('.js-item-link'),
	]);

  	if (vp.label !== 'phone') {
		// open the download modal
	  	let downloadModal = await Promise.all([
			page.waitFor('#downloadModal', {visible: true}),
			page.waitFor(1000),
	  		page.click('.obj-buttons__download-image')
	  	]);
	  	// click the download button
	  	let downloadImage = await Promise.all([
	  		page.waitForNavigation(),
	  		page.click('#downloadModal .btn-primary')
	  	]);
	  	// press the back button to get back to item page
	  	let backBtn = await page.goBack();
	}
	// press the back button to get back to search results
	let backBtn = await page.goBack();

  	// click 'next' on search results to paginate
  	nextBtn = (vp.label === 'phone') ? '.button__next' : '.js-next';
  	let nextResults = await Promise.all([
  		page.waitForResponse(response => response.status() === 200),
  		page.waitFor(1000),
  		page.click(nextBtn),
  	]);

  	// make sure results found is still the same
	let newResultsFound = await page.$eval('.text__collections-heading', el => el.innerText);
	if (newResultsFound !== resultsFound) {
		throw new Error("results found after navigating 'back' don't match original number of results found");
	}

	// remove doctor pill
	let removeDoctor = await Promise.all([
		page.waitForResponse(response => response.status() === 200),
		page.waitFor(1000),
		page.click('.js-refine-filter-pill')
	]);
};
