/**
 * Sample JavaScript file for AST testing.
 */

const fs = require("fs");
const { helper } = require("./utils");

/**
 * Calculate total price.
 */
function calculateTotal(items) {
  return items.reduce((sum, item) => sum + item.price, 0);
}

const formatCurrency = (amount) => {
  return `$${amount.toFixed(2)}`;
};

module.exports = {
  calculateTotal,
  formatCurrency,
};
