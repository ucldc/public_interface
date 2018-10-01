module.exports = {
  plugins: [
    require('postcss-import'),
    require('autoprefixer')({
      browsers: ['> 1%', 'last 2 versions', 'Firefox ESR', 'Opera 12.1', 'Firefox >= 24.0', 'Safari >= 5.1']
    }),
    require('postcss-svg')({
      dirs: 'icons/',
      svgo: {}
    })
  ]
}