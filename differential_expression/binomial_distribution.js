// Copyright 2017 Verily Life Sciences Inc.
//
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

// Basic implementations of the probability mass function and the cumulative
// distribution function for the binomial distribution.
// https://en.wikipedia.org/wiki/Binomial_distribution

// This implementation could be improved.  Compare to the R implementation
// which is a lot more involved.
// - https://fossies.org/dox/R-3.3.3/pbinom_8c_source.html
// - https://fossies.org/dox/R-3.3.3/toms708_8c_source.html#l00243

function dbinom_logspace(k, n, p) {
  if (k < 0 || k > n || n <= 0) return 0.0;
  if (p < 0 || p > 1) return NaN;
  var log_coeff = 0; // Math.log(1)
  for (var i = 1; i <= k; i++) {
    log_coeff = log_coeff + Math.log(n-i+1) - Math.log(i);
  }
  return log_coeff + k*Math.log(p) + (n-k)*Math.log(1-p);
}

function dbinom(k, n, p) {
  return Math.exp(dbinom_logspace(k, n, p));
}

function pbinom(k, n, p) {
  if (k < 0 || k > n || n <= 0) return 0.0;
  if (p < 0 || p > 1) return NaN;
  var log_p = Math.log(p);
  var log_pm1 = Math.log(1-p);
  var log_coeff = 0;  // Math.log(1)
  var pvalue = Math.pow(1-p, n);
  for (var i = 1; i <= k; i++) {
    log_coeff = log_coeff + Math.log(n-i+1) - Math.log(i);
    pvalue = pvalue + Math.exp(log_coeff + i*log_p + (n-i)*log_pm1);
  }
  return pvalue;
}
