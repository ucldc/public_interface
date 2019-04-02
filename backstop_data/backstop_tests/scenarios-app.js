module.exports = options => { 
    return [
        {
            "label": "BackstopJS Homepage",
            "cookiePath": "backstop_data/engine_scripts/cookies.json",
            "url": "https://garris.github.io/BackstopJS/",
            "referenceUrl": "",
            "readyEvent": "",
            "readySelector": "",
            "delay": 10,
            "hideSelectors": [],
            "removeSelectors": [],
            "hoverSelector": "",
            "clickSelector": "",
            "postInteractionWait": 0,
            "selectors": [],
            "selectorExpansion": true,
            "expect": 0,
            "misMatchThreshold" : 0.1,
            "requireSameDimensions": true
        }, 
        {
            "label": "PJAX Back After Download",
            "url": options.urlRoot + "/UCSF/items/",
            "referenceUrl": options.referenceUrlRoot + "/UCSF/items/",
            "onReadyScript": "puppet/kelsiBug.js"
        },
        // {
        //     "label": "Collections Random Explore",
        //     "url": options.urlRoot + "/collections/",
        //     "referenceUrl": options.referenceUrlRoot + "/collections/"
        // },
        {
            "label": "Collections A-Z",
            "url": options.urlRoot + "/collections/num/",
            "referenceUrl": options.referenceUrlRoot + "/collections/num/"
        },
        {
            "label": "Collections Title Search",
            "url": options.urlRoot + "/collections/titleSearch/",
            "referenceUrl": options.referenceUrlRoot + "/collections/titleSearch/"
        },
        {
            "label": "Collection",
            "url": options.urlRoot + "/collections/26098/",
            "referenceUrl": options.referenceUrlRoot + "/collections/26098/"
        },
        {
            "label": "Institutions UC Partners",
            "url": options.urlRoot + "/institutions/",
            "referenceUrl": options.referenceUrlRoot + "/institutions/"
        },
        {
            "label": "Institutions Statewide Partners",
            "url": options.urlRoot + "/institutions/statewide-partners/",
            "referenceUrl": options.referenceUrlRoot + "/institutions/statewide-partners/"
        },
        {
            "label": "Institution Campus Home",
            "url": options.urlRoot + "/UCB/",
            "referenceUrl": options.referenceUrlRoot + "/UCB/"
        },
        {
            "label": "Institution Campus Contributors",
            "url": options.urlRoot + "/UCB/institutions/",
            "referenceUrl": options.referenceUrlRoot + "/UCB/institutions/"
        },
        {
            "label": "Institution Campus Search",
            "url": options.urlRoot + "/UCB/items/",
            "referenceUrl": options.referenceUrlRoot + "/UCB/items/"
        },
        {
            "label": "Institution Home",
            "url": options.urlRoot + "/institution/4/",
            "referenceUrl": options.referenceUrlRoot + "/institution/4/"
        },
        {
            "label": "Institution Search",
            "url": options.urlRoot + "/institution/4/items/",
            "referenceUrl": options.referenceUrlRoot + "/institution/4/items/"
        },
        {
            "label": "Item Page: Harvested Image",
            "url": options.urlRoot + "/item/ark:/13030/tf0n39n8km/",
            "referenceUrl": options.referenceUrlRoot + "/item/ark:/13030/tf0n39n8km/",
            "delay": 1000
        },
        {
            "label": "Item Page: Harvested Text",
            "url": options.urlRoot + "/item/ark:/13030/hb4489p0wt/",
            "referenceUrl": options.referenceUrlRoot + "/item/ark:/13030/hb4489p0wt/",
            "delay": 1000
        },
        {
            "label": "Item Page: Hosted Image",
            "url": options.urlRoot + "/item/ark:/86086/n28w3d2d/",
            "referenceUrl": options.referenceUrlRoot + "/item/ark:/86086/n28w3d2d/",
            "delay": 1000
        },
        {
            "label": "Item Page: Hosted Video",
            "url": options.urlRoot + "/item/b6c47839-def8-4abc-a268-94464bf53f52/",
            "referenceUrl": options.referenceUrlRoot + "/item/b6c47839-def8-4abc-a268-94464bf53f52/",
            "delay": 1000
        },
        {
            "label": "Item Page: Hosted Audio",
            "url": options.urlRoot + "/item/b96339cf-a900-43a9-87e4-7c20b1799518/",
            "referenceUrl": options.referenceUrlRoot + "/item/b96339cf-a900-43a9-87e4-7c20b1799518/",
            "delay": 1000
        },
        {
            "label": "Item Page: Complex Book-like TIFFs",
            "url": options.urlRoot + "/item/ark:/13030/kt9h4nf6h6/",
            "referenceUrl": options.referenceUrlRoot + "/item/ark:/13030/kt9h4nf6h6/",
            "delay": 1000
        },
        {
            "label": "Item Page: Complex Book-like TIFFs and PDFs",
            "url": options.urlRoot + "/item/ark:/86086/n2ks6rph/",
            "referenceUrl": options.referenceUrlRoot + "/item/ark:/86086/n2ks6rph/",
            "delay": 1000
        },
        {
            "label": "Item Page: Complex Book-like PDFs",
            "url": options.urlRoot + "/item/f992b589-5f01-45f9-84ac-4e743bb8a2b1/",
            "referenceUrl": options.referenceUrlRoot + "/item/f992b589-5f01-45f9-84ac-4e743bb8a2b1/",
            "delay": 1000
        },
        {
            "label": "Item Page: Complex Album-like PDFs, MP3s, and TIFFs",
            "url": options.urlRoot + "/item/2bd6bc96-b5d6-4ebc-bc1c-55ecdcc6fda1/",
            "referenceUrl": options.referenceUrlRoot + "/item/2bd6bc96-b5d6-4ebc-bc1c-55ecdcc6fda1/",
            "delay": 1000
        },
        {
            "label": "Item Page: Complex MultiFormat MOV, MP3s, TXTs",
            "url": options.urlRoot + "/item/4e7a1232-82c0-400a-872d-13e18c1ee2d5/",
            "referenceUrl": options.referenceUrlRoot + "/item/4e7a1232-82c0-400a-872d-13e18c1ee2d5/",
            "delay": 1000
        },
        // {
        //     "label": "Exhibitions Random Explore",
        //     "url": options.urlRoot + "/exhibitions/",
        //     "referenceUrl": options.referenceUrlRoot + "/exhibitions/"
        // },
        {
            "label": "Exhibitions Browse All",
            "url": options.urlRoot + "/exhibitions/browse/all/",
            "referenceUrl": options.referenceUrlRoot + "/exhibitions/browse/all/"
        },
        {
            "label": "Exhibitions Browse Cal History",
            "url": options.urlRoot + "/exhibitions/browse/cal-history/",
            "referenceUrl": options.referenceUrlRoot + "/exhibitions/browse/cal-history/"
        },
        {
            "label": "Exhibitions Browse Cal Cultures",
            "url": options.urlRoot + "/exhibitions/browse/cal-cultures/",
            "referenceUrl": options.referenceUrlRoot + "/exhibitions/browse/cal-cultures/"
        },
        {
            "label": "Exhibitions Browse Jarda",
            "url": options.urlRoot + "/exhibitions/browse/jarda/",
            "referenceUrl": options.referenceUrlRoot + "/exhibitions/browse/jarda/"
        },
        {
            "label": "Exhibitions Browse Uncategorized",
            "url": options.urlRoot + "/exhibitions/browse/uncategorized/",
            "referenceUrl": options.referenceUrlRoot + "/exhibitions/browse/uncategorized/"
        },
        {
            "label": "Exhibitions Title Search",
            "url": options.urlRoot + "/exhibitions/search/",
            "referenceUrl": options.referenceUrlRoot + "/exhibitions/search/"
        },
        {
            "label": "Exhibitions Title Search 'Native Americans'",
            "url": options.urlRoot + "/exhibitions/search/?title=Native+Americans",
            "referenceUrl": options.referenceUrlRoot + "/exhibitions/search/?title=Native+Americans"
        },
        {
            "label": "Static Pages: About",
            "url": options.urlRoot + "/about/",
            "referenceUrl": options.referenceUrlRoot + "/about/"
        },
        {
            "label": "Static Pages: Contact",
            "url": options.urlRoot + "/contact/",
            "referenceUrl": options.referenceUrlRoot + "/contact/"
        },
        {
            "label": "Static Pages: Help",
            "url": options.urlRoot + "/help/",
            "referenceUrl": options.referenceUrlRoot + "/help/"
        },
        {
            "label": "Static Pages: Terms of Use",
            "url": options.urlRoot + "/terms/",
            "referenceUrl": options.referenceUrlRoot + "/terms/"
        },
        {
            "label": "Static Pages: For Educators",
            "url": options.urlRoot + "/for-educators/",
            "referenceUrl": options.referenceUrlRoot + "/for-educators/"
        },
        {
            "label": "Static Pages: Contribute",
            "url": options.urlRoot + "/contribute/",
            "referenceUrl": options.referenceUrlRoot + "/contribute/"
        },
        {
            "label": "Static Pages: Outreach",
            "url": options.urlRoot + "/outreach/",
            "referenceUrl": options.referenceUrlRoot + "/outreach/"
        },
        {
            "label": "Static Pages: Posters",
            "url": options.urlRoot + "/posters/",
            "referenceUrl": options.referenceUrlRoot + "/posters/"
        },
        {
            "label": "Theme",
            "url": options.urlRoot + "/exhibitions/t11/jarda/",
            "referenceUrl": options.referenceUrlRoot + "/exhibitions/t11/jarda/"
        },
        {
            "label": "Exhibition",
            "url": options.urlRoot + "/exhibitions/67/jarda-personal-experiences/",
            "referenceUrl": options.referenceUrlRoot + "/exhibitions/67/jarda-personal-experiences/"
        },
        {
            "label": "Exhibition Item with Custom Metadata",
            "url": options.urlRoot + "/exhibitions/88/items/47c4fb71-b1e7-4af8-b759-96f7d3ba2fac/",
            "referenceUrl": options.referenceUrlRoot + "/exhibitions/88/items/47c4fb71-b1e7-4af8-b759-96f7d3ba2fac/"
        },
        {
            "label": "Essay",
            "url": options.urlRoot + "/exhibitions/essay/8/relocation/",
            "referenceUrl": options.referenceUrlRoot + "/exhibitions/essay/8/relocation/"
        },
        {
            "label": "Lesson Plan",
            "url": options.urlRoot + "/for-educators/3/how-do-men-you-become-great/",
            "referenceUrl": options.referenceUrlRoot + "/for-educators/3/how-do-men-you-become-great/"
        },
    ];
}