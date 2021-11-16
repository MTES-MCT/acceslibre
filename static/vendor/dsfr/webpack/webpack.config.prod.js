const Webpack = require('webpack');
const path = require('path');
const merge = require('webpack-merge');
const TerserJSPlugin = require('terser-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const CssoWebpackPlugin = require('csso-webpack-plugin').default;
const common = require('./webpack.common.js');
const fs = require('fs');
const renderPage = require('./renderPage');
const { sassVarsLoader, jsVarsLoader } = require('./varsLoaders');
const global = require('../package.json').config;
const packages = require('./packages');

const entriesPck = {index: './scripts/index.js'};

packages.forEach((pck) => {

  let id = pck.id;
  entriesPck[id] = './packages/' + id + '/_main.scss';

});

const configPackages = merge(common, {
  mode: 'production',
  devtool: 'source-map',
  stats: 'errors-only',
  bail: true,
  optimization: {
    minimizer: [new TerserJSPlugin({})],
  },
  plugins: [
    new Webpack.DefinePlugin({
      'process.env.NODE_ENV': JSON.stringify('production')
    }),
    new Webpack.optimize.ModuleConcatenationPlugin(),
    new MiniCssExtractPlugin({
      filename: 'css/[name].css'
    })
  ],
  module: {
    rules: [
      {
        test: /\.s?css/i,
        use : [
          'css-loader',
          'sass-loader',
          sassVarsLoader
        ]
      },
      {
        test: /\.s?css/i,
        use : [
          {
            loader: MiniCssExtractPlugin.loader,
          },
          'css-loader',
          'sass-loader',
          sassVarsLoader
        ]
      },
      {
        test: /\.(ico|jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2)(\?.*)?$/,
        use: {
          loader: 'file-loader',
          options: {
            name: '../fonts/[name].[ext]'
          },
        },
      },
    ]
  }
});

const cssPackages = Object.assign({}, configPackages,{
  entry: entriesPck,
  output: {
    path: path.join(__dirname, '../dist/packages'),
    filename: 'js/[name].[chunkhash:8].js',
    chunkFilename: 'js/[name].[chunkhash:8].chunk.js'
  }
});

const configGlobal = merge(common, {
  mode: 'none',
  devtool: 'source-map',
  stats: 'errors-only',
  optimization: {
    minimizer: [new TerserJSPlugin({}), new OptimizeCSSAssetsPlugin({})],
  },
  plugins: [
    new Webpack.DefinePlugin({
      'process.env.NODE_ENV': JSON.stringify('production')
    }),
    new MiniCssExtractPlugin({
      filename: "css/dsfr.css",
    }),
    new CssoWebpackPlugin({ pluginOutputPostfix: 'min' })
  ],
  module: {
    rules: [
      {
        test: /\.(ico|jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2)(\?.*)?$/,
        use: {
          loader: 'file-loader',
          options: {
            name: '../fonts/[name].[ext]',
          },
        },
      },
      {
        test: /\.scss$/,
        use : [
          {
            loader: MiniCssExtractPlugin.loader
          },
          'css-loader',
          'sass-loader',
          sassVarsLoader
        ]
      }
    ]
  }
})

const cssGlobal = Object.assign({}, configGlobal,{
  entry: './scripts/global.js',
  output: {
    filename: 'js/[name].[chunkhash:8].js',
    chunkFilename: 'js/[name].[chunkhash:8].chunk.js',
    path: path.join(__dirname, '../dist'),
  }
});


module.exports = [
  cssPackages, cssGlobal
];
