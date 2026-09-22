<?php
/**
 * Shared helpers for the two public form endpoints.
 */
declare(strict_types=1);

const SUCCESS_URL = '/healabspharma/frontend/html/success.html';
const REJECT_URL  = '/healabspharma/frontend/html/reject.html';

/** Redirect and stop. */
function go(string $url)
{
    header('Location: ' . $url);
    exit();
}

function succeed()
{
    go(SUCCESS_URL);
}

function fail(string $reason)
{
    go(REJECT_URL . '?error=' . urlencode($reason));
}

/**
 * Trim, strip control characters and cap length.
 * Replaces FILTER_SANITIZE_STRING, which was deprecated in 8.1 and removed later.
 * Values are stored raw and must be escaped wherever they are displayed.
 */
function clean_text($value, int $maxLength): string
{
    $value = trim((string) $value);
    $stripped = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $value);
    if ($stripped === null) {
        // Input was not valid UTF-8; fall back to a byte-wise strip.
        $stripped = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/', '', $value);
    }
    $stripped = (string) $stripped;

    return function_exists('mb_substr')
        ? mb_substr($stripped, 0, $maxLength)
        : substr($stripped, 0, $maxLength);
}

/** Only accept POST; anything else goes back to the site. */
function require_post()
{
    if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
        go('/');
    }
}

/**
 * Honeypot: bots fill every field they find, humans never see this one.
 * A filled "website" field is silently treated as success so the bot moves on.
 */
function reject_bots()
{
    if (trim((string) ($_POST['website'] ?? '')) !== '') {
        succeed();
    }
}

/**
 * Strip CR/LF so a value can never be used to inject extra mail headers.
 * clean_text() deliberately preserves newlines for the message body, so
 * anything bound for a header must come through here as well.
 */
function header_safe($value): string
{
    return trim(str_replace(["\r", "\n"], ' ', (string) $value));
}

/** Load the backend config once. */
function form_config(): array
{
    static $config = null;
    if ($config === null) {
        $path = __DIR__ . '/config.php';
        $config = is_file($path) ? (array) require $path : [];
    }
    return $config;
}

/**
 * Email an enquiry notification.
 *
 * Returns true only if the mail was handed off successfully. Never throws —
 * a notification failure must not cost us the submission, which is already
 * recorded in the database.
 */
function notify(string $subject, string $body, string $replyToEmail = '', string $replyToName = ''): bool
{
    $config = form_config();
    $to = $config['notifyTo'] ?? [];
    $from = trim((string) ($config['notifyFrom'] ?? ''));

    if (!$to || $from === '') {
        // Not configured yet — see config.example.php.
        return false;
    }

    $headers = [
        'From: Heal Labs Website <' . header_safe($from) . '>',
        'Content-Type: text/plain; charset=UTF-8',
        'X-Mailer: healabs-site',
    ];

    if ($replyToEmail !== '' && filter_var($replyToEmail, FILTER_VALIDATE_EMAIL)) {
        $name = header_safe($replyToName);
        $headers[] = $name !== ''
            ? 'Reply-To: ' . $name . ' <' . header_safe($replyToEmail) . '>'
            : 'Reply-To: ' . header_safe($replyToEmail);
    }

    $ok = false;
    foreach ((array) $to as $recipient) {
        $recipient = header_safe($recipient);
        if (!filter_var($recipient, FILTER_VALIDATE_EMAIL)) {
            continue;
        }
        if (@mail($recipient, header_safe($subject), $body, implode("\r\n", $headers))) {
            $ok = true;
        } else {
            error_log('healabs: notification to ' . $recipient . ' could not be sent');
        }
    }

    return $ok;
}

/** A short line of request context for the notification body. */
function request_context(): string
{
    return sprintf(
        "Submitted: %s\nIP: %s\nPage: %s",
        date('Y-m-d H:i:s T'),
        header_safe($_SERVER['REMOTE_ADDR'] ?? 'unknown'),
        header_safe($_SERVER['HTTP_REFERER'] ?? 'unknown')
    );
}
