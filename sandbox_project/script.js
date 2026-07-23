// Sample data for products
const products = [
    { name: 'Skateboard 1', image: 'skateboard1.jpg', price: '$50' },
    { name: 'Skateboard 2', image: 'skateboard2.jpg', price: '$60' },
    { name: 'Skateboard 3', image: 'skateboard3.jpg', price: '$70' }
];

// Function to create a product item element
function createProductItem(product) {
    const item = document.createElement('div');
    item.className = 'product-item';
    item.innerHTML = `\n        <img src="${product.image}" alt="${product.name}">
        <h2>${product.name}</h2>
        <p>${product.price}</p>
    `;
    return item;
}

// Function to load products into the product list
function loadProducts() {
    const productList = document.querySelector('.product-list');
    products.forEach(product => {
        const item = createProductItem(product);
        productList.appendChild(item);
    });
}

// Load products when the page loads
window.onload = loadProducts;