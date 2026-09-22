<?php
/**
 * Creates a mysqli connection in exception mode.
 * Returns the connection; never echoes credentials or raw driver errors.
 */
declare(strict_types=1);

mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);

$configPath = __DIR__ . '/config.php';
if (!is_file($configPath)) {
    error_log('healabs: backend/config.php is missing — copy config.example.php and fill it in.');
    http_response_code(500);
    exit('Server configuration error.');
}

$config = require $configPath;

try {
    $conn = new mysqli(
        $config['host'],
        $config['user'],
        $config['password'],
        $config['database']
    );
    $conn->set_charset($config['charset'] ?? 'utf8mb4');
} catch (Throwable $e) {
    // Log the detail; show the visitor nothing useful to an attacker.
    error_log('healabs: database connection failed — ' . $e->getMessage());
    header('Location: /healabspharma/frontend/html/reject.html?error=' . urlencode('server'));
    exit();
}

return $conn;
