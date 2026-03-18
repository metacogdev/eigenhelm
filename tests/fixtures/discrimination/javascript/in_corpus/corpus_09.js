/*!
 * express
 * Copyright(c) 2009-2013 TJ Holowaychuk
 * Copyright(c) 2014-2015 Douglas Christopher Wilson
 * MIT Licensed
 */

'use strict';

/**
 * Module dependencies.
 * @private
 */

var contentDisposition = require('content-disposition');
var createError = require('http-errors')
var deprecate = require('depd')('express');
var encodeUrl = require('encodeurl');
var escapeHtml = require('escape-html');
var http = require('node:http');
var onFinished = require('on-finished');
var mime = require('mime-types')
var path = require('node:path');
var pathIsAbsolute = require('node:path').isAbsolute;
var statuses = require('statuses')
var sign = require('cookie-signature').sign;
var normalizeType = require('./utils').normalizeType;
var normalizeTypes = require('./utils').normalizeTypes;
var setCharset = require('./utils').setCharset;
var cookie = require('cookie');
var send = require('send');
var extname = path.extname;
var resolve = path.resolve;
var vary = require('vary');
const { Buffer } = require('node:buffer');

/**
 * Response prototype.
 * @public
 */

var res = Object.create(http.ServerResponse.prototype)

/**
 * Module exports.
 * @public
 */

module.exports = res

/**
 * Set the HTTP status code for the response.
 *
 * Expects an integer value between 100 and 999 inclusive.
 * Throws an error if the provided status code is not an integer or if it's outside the allowable range.
 *
 * @param {number} code - The HTTP status code to set.
 * @return {ServerResponse} - Returns itself for chaining methods.
 * @throws {TypeError} If `code` is not an integer.
 * @throws {RangeError} If `code` is outside the range 100 to 999.
 * @public
 */

res.status = function status(code) {
  // Check if the status code is not an integer
  if (!Number.isInteger(code)) {
    throw new TypeError(`Invalid status code: ${JSON.stringify(code)}. Status code must be an integer.`);
  }
  // Check if the status code is outside of Node's valid range
  if (code < 100 || code > 999) {
    throw new RangeError(`Invalid status code: ${JSON.stringify(code)}. Status code must be greater than 99 and less than 1000.`);
  }

  this.statusCode = code;
  return this;
};

/**
 * Set Link header field with the given `links`.
 *
 * Examples:
 *
 *    res.links({
 *      next: 'http://api.example.com/users?page=2',
 *      last: 'http://api.example.com/users?page=5',
 *      pages: [
 *        'http://api.example.com/users?page=1',
 *        'http://api.example.com/users?page=2'
 *      ]
 *    });
 *
 * @param {Object} links
 * @return {ServerResponse}
 * @public
 */

res.links = function(links) {
  var link = this.get('Link') || '';
  if (link) link += ', ';
  return this.set('Link', link + Object.keys(links).map(function(rel) {
    // Allow multiple links if links[rel] is an array
    if (Array.isArray(links[rel])) {
      return links[rel].map(function (singleLink) {
        return `<${singleLink}>; rel="${rel}"`;
      }).join(', ');
    } else {
      return `<${links[rel]}>; rel="${rel}"`;
    }
  }).join(', '));
};

/**
 * Send a response.
 *
 * Examples:
 *
 *     res.send(Buffer.from('wahoo'));
 *     res.send({ some: 'json' });
 *     res.send('<p>some html</p>');
 *
 * @param {string|number|boolean|object|Buffer} body
 * @public
 */

res.send = function send(body) {
  var chunk = body;
  var encoding;
  var req = this.req;
  var type;

  // settings
  var app = this.app;

  switch (typeof chunk) {
    // string defaulting to html
    case 'string':
      if (!this.get('Content-Type')) {
        this.type('html');
      }
      break;
    case 'boolean':
    case 'number':
    case 'object':
      if (chunk === null) {
        chunk = '';
      } else if (ArrayBuffer.isView(chunk)) {
        if (!this.get('Content-Type')) {
          this.type('bin');
        }
      } else {
