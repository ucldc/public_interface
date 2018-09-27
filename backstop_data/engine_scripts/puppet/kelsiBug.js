// references bug https://www.pivotaltracker.com/story/show/151812193
// where after a user downloads an image and navigates back to search results
// the search results page has lost context despite initally looking the same
// (can't paginate forward, X out search within pill)

function promiseTimeout(ms, promise){

  return new Promise(function(resolve, reject){

    // create a timeout to reject promise if not resolved
    var timer = setTimeout(function(){
        reject(new Error("promise timeout"));
    }, ms);

    promise
        .then(function(res){
            clearTimeout(timer);
            resolve(res);
        })
        .catch(function(err){
            clearTimeout(timer);
            reject(err);
        });
  });
};

module.exports = async (page, scenario, vp) => {
	console.log('SCENARIO > ' + scenario.label);
	// await require('./clickAndHoverHelper')(page, scenario);

	// add more ready handlers here...
	let searchWithinElementHandle = await page.$('#search-collection__field');
	await searchWithinElementHandle.type('doctor');

	// search UCSF items for 'doctor' & get number of results found
	await Promise.all([
		page.waitForResponse(response => response.status() === 200),
		searchWithinElementHandle.press('Enter'),
		page.waitForNavigation()
  	]);
  	let resultsFound = await page.$eval('h3.text__collections-heading', el => el.innerText);

  	// click into the first item
	await Promise.all([
		page.waitForNavigation(),
		page.waitFor(1000),
		page.click('.js-item-link'),
	]);

  	if (vp.label !== 'phone') {
		// open the download modal
		await Promise.all([
			page.waitFor('#downloadModal', {visible: true}),
			page.waitFor(1000),
	  		page.click('.obj-buttons__download-image')
	  	]);
		let imgUrl = await page.$eval('#downloadModal .btn-primary', el => el.href);

		// await new tab per comment thread here: https://github.com/GoogleChrome/puppeteer/issues/386
		const browser = page.browser();
		function getNewPageWhenLoaded() {
			return new Promise((x) => browser.once('targetcreated', async (target) => {
				const newPage = await target.page();
				const newPagePromise = new Promise(() => newPage.once('domcontentloaded', () => x(newPage)));
				const isPageLoaded = await newPage.evaluate(() => document.readyState);
				return isPageLoaded.match('complete|interactive') ? x(newPage) : newPagePromise;
			}));
		}
		const newPagePromise = promiseTimeout(6000, getNewPageWhenLoaded());
		await page.click('#downloadModal .btn-primary');
		// sometimes image opens in new tab, sometimes it opens in the same tab
		try {
			const imgPage = await Promise.race([
				newPagePromise,
				page.waitForNavigation()
			]);
			// opened in the same tab
			// press the back button to get back to item page
			if (imgPage.url() === imgUrl) {
				if (page.url() === imgUrl) {
					await page.goBack();
				} else {
					// close the download modal
					await Promise.all([
						page.waitFor('#downloadModal', {visible: false}),
						page.waitFor(1000),
						page.click('#downloadModal .close')
					]);
				}
			} 
		} catch(err) {
			console.log("Didn't open the image for download! " + err);
		}

	}
	// press the back button to get back to search results
	await page.goBack();

  	// click 'next' on search results to paginate
  	nextBtn = (vp.label === 'phone') ? '.button__next' : '.js-next';
	await Promise.all([
  		page.waitForResponse(response => response.status() === 200),
  		page.waitFor(1000),
  		page.click(nextBtn),
  	]);

	try {
		// make sure results found is still the same
		let newResultsFound = await page.$eval('h3.text__collections-heading', el => el.innerText);
		if (newResultsFound !== resultsFound) {
			throw new Error("results found after navigating 'back' don't match original number of results found");
		}
	} catch(err) {
		console.log(err);
	}

	// remove doctor pill
	let removeDoctor = await Promise.all([
		page.waitForResponse(response => response.status() === 200),
		page.waitFor(1000),
		page.click('.js-refine-filter-pill')
	]);
};
