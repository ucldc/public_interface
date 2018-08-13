const del = require('del');
const wiredep = require('gulp-wiredep');
const sass = require('gulp-sass');
const sassLint = require('gulp-sass-lint');
const postcss = require('gulp-postcss');
const sourcemaps = require('gulp-sourcemaps');
const minifyCSS = require('gulp-clean-css');

const browserSync = require('browser-sync');
const reload = browserSync.reload;

const fileinclude = require('gulp-file-include');

const jshint = require('gulp-jshint');
const stylish = require('jshint-stylish');
const gulp = require('gulp');

gulp.task('sass-build', function() {
 return gulp.src('app/{,*/}*.scss')
  .pipe(wiredep({
    ignorePath: /(\.\.\/){1,2}bower_components\//
  }))
  .pipe(sassLint({
    configFile: 'sass-lint-config.yml'
  }))
  .pipe(sassLint.format())
  .pipe(sassLint.failOnError())
  .pipe(sass({
    includePaths: ['bower_components/*']
  }).on('error', sass.logError))
  .pipe(postcss())
  .pipe(minifyCSS())
  .pipe(gulp.dest('.tmp'));
});

gulp.task('sass-serve', function() {
 return gulp.src('app/{,*/}*.scss')
  .pipe(sourcemaps.init())
  .pipe(wiredep({
    ignorePath: /(\.\.\/){1,2}bower_components\//
  }))
  // .pipe(sassLint({
  //   configFile: 'sass-lint-config.yml'
  // }))
  // .pipe(sassLint.format())
  // .pipe(sassLint.failOnError())
  .pipe(sass({
    includePaths: ['bower_components/*']
  }).on('error', sass.logError))
  .pipe(postcss())
  .pipe(sourcemaps.write('sourcemaps'))
  .pipe(gulp.dest('.tmp'));
});

gulp.task('copy-css', function() {
	return gulp.src('./app/{,*/}*.css')
		.pipe(gulp.dest('.tmp'));
});

gulp.task('js-serve', function() {
	return gulp.src('app/{,*/}*.js')
		.pipe(jshint())
		.pipe(jshint.reporter(stylish))
    .pipe(gulp.dest('.tmp'))
});

gulp.task('html-build', function(done) {
	gulp.src('./app/*.html')
		.pipe(fileinclude({
			basepath: 'app/'
		}))
		.pipe(wiredep({
			ignorePath: /^\/|\.\.\//,
			exclude: ['bower_components/bootstrap-sass-official/assets/javascripts/bootstrap.js']
		}))
		.pipe(gulp.dest('.tmp'));
	done();
});

gulp.task('clean', function() { return del(['./.tmp']); });

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
  gulp.watch(['admin/*', 'scripts/{,*/}*.js'], {cwd: 'app'}, reload);

  gulp.watch(['bower.json'], gulp.parallel('html-build', 'sass-serve'));
  gulp.watch(['gulpfile.js']);
  gulp.watch(['app/{,*/}*.scss'], gulp.parallel('sass-serve'));
  gulp.watch(['app/{,*/}*.css'], gulp.parallel('copy-css'));
  gulp.watch(['app/{,*/}*.js'], gulp.parallel('js-serve'));
});

gulp.task('serve', gulp.series('clean',
	gulp.parallel('html-build', 'sass-serve', 'copy-css', 'js-serve'), 'runserver'));