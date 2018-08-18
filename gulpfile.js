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

gulp.task('js-build', function() {
  return gulp.src('app/scripts/{,**/}*.js')
    .pipe(jshint())
    .pipe(jshint.reporter(stylish))
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
  return gulp.src('./app/*.html')
  .pipe(wiredep())
  .pipe(fileinclude({
    basepath: 'app/'
  }))
  .pipe(gulp.dest('.tmp'));
});

gulp.task('html-build', function(done) {
  return gulp.src('./app/*.html')
  .pipe(wiredep())
  .pipe(useref({ searchPath: 'dist' }))
  .pipe(fileinclude({
    basepath: 'app/'
  }))
  .pipe(gulp.dest('dist'));
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
        '/styles/fonts': 'app/styles/fonts'
      },
		}, 
    middleware: [
      function (req, res, next) {
        res.setHeader('Access-Control-Allow-Origin', '*');
        next();
      }
    ],
    port: 9000
	});

  gulp.watch(['.tmp/*'], reload);
  gulp.watch(['app/admin/*'], reload);
  gulp.watch(['gulpfile.js']);
  gulp.watch(['bower.json', 'app/{,**/}*.html'], gulp.parallel('html-serve'));
  gulp.watch(['app/{,**/}*.scss'], gulp.parallel('sass-serve'));
  gulp.watch(['app/{,**/}*.js'], gulp.parallel('js-serve'));
});

gulp.task('serve', gulp.series('clean',
	gulp.parallel('html-serve', 'sass-serve', 'js-serve'), 'runserver'));

gulp.task('build', gulp.series('clean', gulp.parallel('sass-build', 'js-build'), 'html-build'));




