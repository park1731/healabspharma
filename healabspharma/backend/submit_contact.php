<?php
/**
 * Contact form endpoint.
 *
 * Records the enquiry in contact_inquiries AND emails it to the team. The
 * two are independent on purpose: a lead is only lost if BOTH fail, so a
 * database hiccup or an unconfigured mailbox cannot silently swallow it.
 */
declare(strict_types=1);

require_once __DIR__ . '/form_helpers.php';

require_post();
reject_bots();

// Single-line fields go through header_safe() too — the name reaches a
// Reply-To header, where a newline would allow header injection.
$name    = header_safe(clean_text($_POST['name'] ?? '', 120));
$email   = trim((string) ($_POST['email'] ?? ''));
$phone   = header_safe(clean_text($_POST['phone'] ?? '', 40));
$message = clean_text($_POST['message'] ?? '', 4000);

if ($name === '' || $message === '') {
    fail('missing_fields');
}

if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    fail('invalid_email');
}
$email = function_exists('mb_substr') ? mb_substr($email, 0, 190) : substr($email, 0, 190);

$stored = false;

try {
    /** @var mysqli $conn */
    $conn = require __DIR__ . '/db_connection.php';
    $stmt = $conn->prepare(
        'INSERT INTO contact_inquiries (name, email, phone, message) VALUES (?, ?, ?, ?)'
    );
    $stmt->bind_param('ssss', $name, $email, $phone, $message);
    $stmt->execute();
    $stmt->close();
    $conn->close();
    $stored = true;
} catch (mysqli_sql_exception $e) {
    if ((int) $e->getCode() === 1062) {
        // Already recorded — nothing lost.
        $stored = true;
    } else {
        error_log('healabs: contact insert failed — ' . $e->getMessage());
    }
} catch (Throwable $e) {
    error_log('healabs: contact storage error — ' . $e->getMessage());
}

$body = "New enquiry from the Heal Labs website.\n\n"
      . "Name:    {$name}\n"
      . "Email:   {$email}\n"
      . "Phone:   " . ($phone !== '' ? $phone : '(not given)') . "\n\n"
      . "Message:\n{$message}\n\n"
      . "---\n"
      . request_context() . "\n"
      . ($stored ? '' : "NOTE: this enquiry could NOT be written to the database.\n");

$emailed = notify('Website enquiry from ' . $name, $body, $email, $name);

if ($stored || $emailed) {
    succeed();
}

fail('server');
