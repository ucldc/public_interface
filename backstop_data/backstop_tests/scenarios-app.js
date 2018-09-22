module.exports = options => { 
    return [
        {
            "label": "BackstopJS Homepage",
            "cookiePath": "backstop_data/engine_scripts/cookies.json",
            "url": "https://garris.github.io/BackstopJS/",
            "referenceUrl": "",
            "readyEvent": "",
            "readySelector": "",
            "delay": 0,
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
        }
    ];
}