<?php
/**
 * Newsletter signup endpoint.
 *
 * Same belt-and-braces approach as the contact form: store it, email it,
 * and only report failure if neither worked.
 */
declare(strict_types=1);

require_once __DIR__ . '/form_helpers.php';

require_post();
reject_bots();

$email = trim((string) ($_POST['email'] ?? ''));

if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    fail('invalid_email');
}
$email = function_exists('mb_substr') ? mb_substr($email, 0, 190) : substr($email, 0, 190);

$stored = false;
$duplicate = false;

try {
    /** @var mysqli $conn */
    $conn = require __DIR__ . '/db_connection.php';
    $stmt = $conn->prepare('INSERT INTO newsletter_subscribers (email) VALUES (?)');
    $stmt->bind_param('s', $email);
    $stmt->execute();
    $stmt->close();
    $conn->close();
    $stored = true;
} catch (mysqli_sql_exception $e) {
    if ((int) $e->getCode() === 1062) {
        // Already subscribed — a success from the visitor's point of view,
        // and not worth emailing the team about again.
        $stored = true;
        $duplicate = true;
    } else {
        error_log('healabs: newsletter insert failed — ' . $e->getMessage());
    }
} catch (Throwable $e) {
    error_log('healabs: newsletter storage error — ' . $e->getMessage());
}

$emailed = false;
if (!$duplicate) {
    $body = "New newsletter signup.\n\nEmail: {$email}\n\n---\n" . request_context() . "\n"
          . ($stored ? '' : "NOTE: this signup could NOT be written to the database.\n");
    $emailed = notify('Newsletter signup: ' . $email, $body, $email);
}

if ($stored || $emailed) {
    succeed();
}

fail('server');
