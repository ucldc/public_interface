const del = require('del');
const sass = require('gulp-sass');
const sassLint = require('gulp-sass-lint');
const postcss = require('gulp-postcss');
const sourcemaps = require('gulp-sourcemaps');
const minifyCSS = require('gulp-clean-css');
const useref = require('gulp-useref');
const browserSync = require('browser-sync');
const fileinclude = require('gulp-file-include');
const jshint = require('gulp-jshint');
const uglify = require('gulp-uglify');
const stylish = require('jshint-stylish');
const imagemin = require('gulp-imagemin');
const modernizr = require('gulp-modernizr');
const gulp = require('gulp');
const ghpages = require('gh-pages');
const { spawn } = require('child_process');

gulp.task('sass-build', function() {
 return gulp.src('app/{,**/}*.scss')
  .pipe(sassLint({
    configFile: 'sass-lint-config.yml'
  }))
  .pipe(sassLint.format())
  .pipe(sassLint.failOnError())
  .pipe(sass().on('error', sass.logError))
  .pipe(postcss())
  .pipe(minifyCSS())
  .pipe(gulp.dest('dist'));
});

gulp.task('sass-serve', function() {
 return gulp.src('app/{,**/}*.scss')
  .pipe(sourcemaps.init())
  .pipe(sassLint({
    configFile: 'sass-lint-config.yml'
  }))
  .pipe(sassLint.format())
  .pipe(sassLint.failOnError())
  .pipe(sass().on('error', sass.logError))
  .pipe(postcss())
  .pipe(sourcemaps.write('sourcemaps'))
  .pipe(gulp.dest('.tmp'))
  .pipe(browserSync.stream());
});

gulp.task('minifyCss', function() {
  return gulp.src('./dist/styles/vendor.css', {base: './'})
  .pipe(minifyCSS())
  .pipe(gulp.dest('./'));
});

gulp.task('js-build', function() {
  return gulp.src(['app/scripts/{,**/}*.js', '!app/scripts/ThreeDViewer/**'])
    .pipe(jshint())
    .pipe(jshint.reporter(stylish))
    .pipe(uglify())
    .pipe(gulp.dest('dist/scripts'));
});

gulp.task('minifyJS', function() {
  return gulp.src(['./dist/scripts/vendor.js', './dist/scripts/calisphere.js'], {base: './'})
  .pipe(uglify())
  .pipe(gulp.dest('./'));
});

gulp.task('modernizr', function() {
  return gulp.src('dist/{,**/}*.{css,js}')
    .pipe(modernizr({
      "options": [
        "setClasses",
        "addTest",
        "html5printshiv",
        "testProp"
      ], "excludeTests": ['hidden']
    }))
    .pipe(uglify())
    .pipe(gulp.dest('dist/scripts'));
});

gulp.task('modernizr-serve', function() {
  return gulp.src('.tmp/{,**/}*.{css,js}')
    .pipe(modernizr({
      "options": [
        "setClasses",
        "addTest",
        "html5printshiv",
        "testProp"
      ], "excludeTests": ['hidden']
    }))
    .pipe(gulp.dest('.tmp/scripts'));
});

gulp.task('js-serve', function() {
	return gulp.src(['app/scripts/{,**/}*.js', '!app/scripts/ThreeDViewer/**'])
  .pipe(jshint())
  .pipe(jshint.reporter(stylish))
  .pipe(gulp.dest('.tmp/scripts'));
});

gulp.task('html-serve', function(done) {
  return gulp.src('app/*.html')
  .pipe(fileinclude({
    basepath: 'app/'
  }))
  .pipe(gulp.dest('.tmp'));
});

gulp.task('html-build', function() {
  return gulp.src('app/*.html')
  .pipe(useref({ searchPath: ['dist', '.'] }))
  .pipe(fileinclude({
    basepath: 'app/'
  }))
  // replace html blocks, noAssets set to true - already made bundles
  .pipe(useref({ noAssets: true, searchPath: ['dist', '.'] }))
  .pipe(gulp.dest('dist'));
});

gulp.task('fonts-serve', function() {
  return gulp.src([
    'node_modules/font-awesome/fonts/*',
    'node_modules/slick-carousel/slick/fonts/*.{woff,woff2}',
    'node_modules/source-sans-pro/**/*.{woff,woff2}'])
  .pipe(gulp.dest('.tmp/vendor-fonts'));
});

gulp.task('fonts-build', function() {
  return gulp.src([
    'node_modules/font-awesome/fonts/*',
    'node_modules/slick-carousel/slick/fonts/*.{woff,woff2}',
    'node_modules/source-sans-pro/**/*.{woff,woff2}'])
  .pipe(gulp.dest('dist/vendor-fonts'));
});

gulp.task('copy-ico-png-txt-webp-htaccss', function() {
  return gulp.src([
    'app/*.{ico,png,txt}',
    'app/images/{,**/}*.webp',
    'node_modules/apache-server-configs/dist/.htaccess'])
  .pipe(gulp.dest('dist'));
});

gulp.task('copy-openseadragon-files', function() {
  return gulp.src('node_modules/openseadragon/build/{,**/}*.*')
  .pipe(gulp.dest('dist/node_modules/openseadragon/build/'))
});

gulp.task('image-build', function() {
  return gulp.src([
    'app/images/{,**/}*.{gif,jpeg,jpg,png,svg}',
    'app/styles/{,**/}*.{gif,jpeg,jpg,png,svg}'],
    { base: 'app/' })
  .pipe(imagemin())
  .pipe(gulp.dest('dist/'))
});

gulp.task('clean', function() { return del(['./.tmp', './dist']); });

gulp.task('runserver', function() {
	browserSync({
		server: {
			baseDir: ['.tmp'],
			routes: {
        '/node_modules': './node_modules',
        '/images': 'app/images',
        '/admin': 'app/admin',
        '/vendor-fonts': 'app/vendor-fonts'
      },
		}, 
    notify: false,
    middleware: [
      function (req, res, next) {
        res.setHeader('Access-Control-Allow-Origin', '*');
        next();
      }
    ],
    port: 9000
	});

  // we should watch tests too
  // gulp.watch(['test/spec/{,**/}*.js'], test)
  gulp.watch(['app/**/*.html', 'app/admin/*']).on('change', browserSync.reload);
  gulp.watch(['gulpfile.js']);
  gulp.watch(['app/{,**/}*.html'], gulp.parallel('html-serve'));
  gulp.watch(['app/{,**/}*.scss'], gulp.parallel('sass-serve'));
  gulp.watch(['app/{,**/}*.js'], gulp.parallel('js-serve'));
});

gulp.task('publish', function(cb) {
  return spawn('NODE_DEBUG=gh-pages npm run publish', {
    stdio: 'inherit',
    shell: true,
  });
});

gulp.task('threedviewer-build', function() {
  return spawn('npm run build-threedviewer', {
    stdio: 'inherit',
    shell: true,
  });
});

// we should have tests
gulp.task('test', gulp.series('clean'));

gulp.task('serve', gulp.series('clean',
	gulp.parallel('html-serve', 'sass-serve', 'js-serve'), 'modernizr-serve', 'fonts-serve', 'runserver'));

gulp.task('build', gulp.series('clean', gulp.parallel(
  'sass-build',
  'js-build',
  'image-build',
  'copy-ico-png-txt-webp-htaccss',
  'copy-openseadragon-files'
  ), 'modernizr', 'html-build', 'fonts-build', 'minifyCss', 'minifyJS', 'threedviewer-build'));

gulp.task('default', gulp.series('build'));

gulp.task('serve:dist', gulp.parallel('serve', 'build'));
