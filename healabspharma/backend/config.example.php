<?php
/**
 * Database credentials — copy this file to config.php and fill in real values.
 * config.php is git-ignored and must never be committed.
 */
return [
    'host'     => 'localhost',
    'user'     => 'your_db_user',
    'password' => 'your_db_password',
    'database' => 'your_db_name',
    'charset'  => 'utf8mb4',

    // Where enquiry notifications are sent.
    'notifyTo' => ['you@example.com'],

    // From: address — must be a mailbox on your own domain or mail will be
    // treated as spoofed and filtered. Leave empty to disable notifications.
    'notifyFrom' => 'website@example.com',
];
