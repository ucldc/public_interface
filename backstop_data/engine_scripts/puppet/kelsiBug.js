module.exports = async (page, scenario, vp) => {
  console.log('SCENARIO > ' + scenario.label);
  await require('./clickAndHoverHelper')(page, scenario);

  // add more ready handlers here...
  const searchElementHandle = await page.$('#search-collection__field');
  await searchElementHandle.type('doctor');

  await Promise.all([
  	page.waitForResponse(response => response.status() === 200),
  	searchElementHandle.press('Enter'),
  ]).then(function() {
  	console.log('successfully searched for "doctor"');
  }).catch(function() {
  	console.log('unsuccessfully search for "doctor"');
  });

  await Promise.all([
  	page.waitForNavigation(),
  	page.click('.js-item-link'),
  ]);
};
