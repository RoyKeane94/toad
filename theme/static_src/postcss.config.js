const purgecss = require('@fullhuman/postcss-purgecss')({
  content: [
    '../../**/*.html',
    '../../../templates/**/*.html',
    '../../../**/templates/**/*.html',
  ],
  defaultExtractor: content => content.match(/[\w-./:]+(?<!:)/g) || []
});

const plugins = {
  '@tailwindcss/postcss': {},
  'postcss-simple-vars': {},
  'postcss-nested': {},
};

if (process.env.NODE_ENV === 'production') {
  plugins['@fullhuman/postcss-purgecss'] = {
    content: [
      './pages/templates/**/*.html',
      './accounts/templates/**/*.html',
      './theme/templates/**/*.html',
      '../../pages/templates/**/*.html',
      '../../accounts/templates/**/*.html',
      '../../theme/templates/**/*.html',
    ],
    defaultExtractor: content => content.match(/[\w-/:]+(?<!:)/g) || []
  };
}

module.exports = {
  plugins: plugins
};
