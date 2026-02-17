/**
 * Mock product catalog for the WebMCP demo store.
 * In a real app this would come from a database or API.
 */

window.PRODUCT_CATALOG = [
  {
    id: "p001",
    name: "UltraBook Pro 14",
    category: "laptops",
    price: 899.99,
    stock: 12,
    specs: { cpu: "Intel i7-1355U", ram: "16GB", storage: "512GB SSD" },
    tags: ["laptop", "ultrabook", "portable", "work"],
  },
  {
    id: "p002",
    name: "GamerX RTX Laptop",
    category: "laptops",
    price: 1499.99,
    stock: 5,
    specs: { cpu: "AMD Ryzen 9", ram: "32GB", storage: "1TB NVMe", gpu: "RTX 4070" },
    tags: ["laptop", "gaming", "rtx", "high-performance"],
  },
  {
    id: "p003",
    name: "BudgetBook Essential",
    category: "laptops",
    price: 399.99,
    stock: 28,
    specs: { cpu: "Intel Celeron N4500", ram: "8GB", storage: "256GB eMMC" },
    tags: ["laptop", "budget", "student", "basic"],
  },
  {
    id: "p004",
    name: "MechKey Pro Keyboard",
    category: "peripherals",
    price: 149.99,
    stock: 50,
    specs: { switch: "Cherry MX Red", backlight: "RGB", layout: "TKL" },
    tags: ["keyboard", "mechanical", "gaming", "peripheral"],
  },
  {
    id: "p005",
    name: "4K UltraWide Monitor",
    category: "monitors",
    price: 649.99,
    stock: 8,
    specs: { resolution: "3840x1600", size: "34-inch", refresh: "144Hz", panel: "IPS" },
    tags: ["monitor", "4k", "ultrawide", "productivity"],
  },
  {
    id: "p006",
    name: "ErgoMouse Wireless",
    category: "peripherals",
    price: 79.99,
    stock: 100,
    specs: { dpi: "400-3200", buttons: 6, battery: "12 months" },
    tags: ["mouse", "ergonomic", "wireless", "peripheral"],
  },
  {
    id: "p007",
    name: "Noise-Cancel Headset",
    category: "audio",
    price: 249.99,
    stock: 15,
    specs: { driver: "40mm", anc: true, battery: "30h", mic: "detachable boom" },
    tags: ["headset", "anc", "noise-cancelling", "audio", "work"],
  },
  {
    id: "p008",
    name: "USB-C Hub 10-in-1",
    category: "accessories",
    price: 59.99,
    stock: 75,
    specs: { ports: "HDMI 4K, 3×USB-A, USB-C PD 100W, SD/microSD, Ethernet, 3.5mm" },
    tags: ["hub", "usb-c", "dock", "accessory"],
  },
];

window.SHOPPING_CART = [];
