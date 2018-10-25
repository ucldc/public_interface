const del = require('del');
const wiredep = require('gulp-wiredep');
const sass = require('gulp-sass');
const sassLint = require('gulp-sass-lint');
const postcss = require('gulp-postcss');
const sourcemaps = require('gulp-sourcemaps');
const minifyCSS = require('gulp-clean-css');
const useref = require('gulp-useref');
const browserSync = require('browser-sync');
const reload = browserSync.reload;
const fileinclude = require('gulp-file-include');
const jshint = require('gulp-jshint');
const uglify = require('gulp-uglify');
const stylish = require('jshint-stylish');
const imagemin = require('gulp-imagemin');
const modernizr = require('gulp-modernizr');
const gulp = require('gulp');

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
  .pipe(gulp.dest('.tmp'));
});

gulp.task('minifyCss', function() {
  return gulp.src('./dist/styles/vendor.css', {base: './'})
  .pipe(minifyCSS())
  .pipe(gulp.dest('./'));
});

gulp.task('js-build', function() {
  return gulp.src('app/scripts/{,**/}*.js')
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
    .pipe(modernizr())
    .pipe(uglify())
    .pipe(gulp.dest('dist/scripts'));
});

gulp.task('js-serve', function() {
	return gulp.src('app/scripts/{,**/}*.js')
  .pipe(jshint())
  .pipe(jshint.reporter(stylish))
  .pipe(gulp.dest('.tmp/scripts'));
});

gulp.task('html-serve', function(done) {
  return gulp.src('app/*.html')
  .pipe(wiredep())
  .pipe(fileinclude({
    basepath: 'app/'
  }))
  .pipe(gulp.dest('.tmp'));
});

gulp.task('html-build', function() {
  return gulp.src('app/*.html')
  .pipe(wiredep())
  .pipe(useref({ searchPath: 'dist' }))
  .pipe(fileinclude({
    basepath: 'app/'
  }))
  // replace html blocks, noAssets set to true - already made bundles
  .pipe(useref({ noAssets: true, searchPath: 'dist' }))
  .pipe(gulp.dest('dist'));
});

gulp.task('copy-ico-png-txt-webp-htaccss', function() {
  return gulp.src([
    'app/*.{ico,png,txt}',
    'app/images/{,**/}*.webp',
    'node_modules/apache-server-configs/dist/.htaccess'])
  .pipe(gulp.dest('dist'));
});

gulp.task('copy-bower-files', function() {
  return gulp.src('bower_components/openseadragon/built-openseadragon/{,**/}*.*')
  .pipe(gulp.dest('dist/bower_components/openseadragon/built-openseadragon/'))
})

gulp.task('copy-fonts', function() {
  return gulp.src([
    'app/styles/vendor-fonts/{,**/}*.*',
    'app/vendor-fonts/{,**/}*.*'
  ], { base: 'app'})
  .pipe(gulp.dest('dist/'));
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
        '/bower_components': './bower_components',
        '/images': 'app/images',
        '/admin': 'app/admin',
        '/static_root/vendor-fonts': 'app/styles/vendor-fonts',
        '/vendor-fonts': 'app/styles/vendor-fonts',
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
  gulp.watch(['.tmp/*'], reload);
  gulp.watch(['app/admin/*'], reload);
  gulp.watch(['gulpfile.js']);
  gulp.watch(['bower.json', 'app/{,**/}*.html'], gulp.parallel('html-serve'));
  gulp.watch(['app/{,**/}*.scss'], gulp.parallel('sass-serve'));
  gulp.watch(['app/{,**/}*.js'], gulp.parallel('js-serve'));
});

// we should have tests
gulp.task('test', gulp.series('clean'));

gulp.task('serve', gulp.series('clean',
	gulp.parallel('html-serve', 'sass-serve', 'js-serve'), 'runserver'));

gulp.task('build', gulp.series('clean', gulp.parallel(
  'sass-build',
  'js-build',
  'image-build',
  'copy-ico-png-txt-webp-htaccss',
  'copy-fonts',
  'copy-bower-files'
  ), 'modernizr', 'html-build', 'minifyCss', 'minifyJS'));

gulp.task('default', gulp.series('build'));

gulp.task('serve:dist', gulp.parallel('serve', 'build'));
