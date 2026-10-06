#!/usr/bin/perl
use strict; use warnings;
use File::Basename;
use File::Path qw(make_path);

my $outDir = 'assets/pages';
make_path($outDir);

my @files = @ARGV;
for my $f (@files) {
    open(my $fh, '<:raw', $f) or die "read $f: $!";
    local $/; my $html = <$fh>; close $fh;

    my $dir = dirname($f);
    my $base = basename($f, '.html');
    my $cssName = $base;
    $cssName =~ s/\s+/-/g;
    my $prefix = ($dir eq '.') ? '' : '../';

    if ($html =~ m{<style>(.*?)</style>}s) {
        my $css = $1;
        # leading/trailing blank lines trimmed
        $css =~ s/^\s+//; $css =~ s/\s+$//;
        my $out = "/* تفکیک‌شده از $base.html — فقط متغیرهای اختصاصی همین صفحه */\n$css\n";
        open(my $o, '>:raw', "$outDir/$cssName.css") or die "write: $!";
        print $o $out; close $o;

        $html =~ s{\s*<style>.*?</style>}{}s;
        print "extracted: $f -> $outDir/$cssName.css\n";
    }

    # link the extracted css (if it exists) right after the main stylesheet link
    if (-e "$outDir/$cssName.css") {
        my $link = '<link rel="stylesheet" href="' . $prefix . 'assets/pages/' . $cssName . '.css">';
        unless ($html =~ /\Q$link\E/) {
            $html =~ s{(<link rel="stylesheet" href="[^"]*assets/style\.css">)}{$1\n$link}s
                or die "stylesheet link not found in $f";
        }
    }

    # add the fit script before </body>
    my $script = '<script src="' . $prefix . 'assets/fit.js" defer></script>';
    unless ($html =~ /\Q$script\E/) {
        $html =~ s{</body>}{$script\n</body>}s or die "</body> not found in $f";
    }

    open(my $w, '>:raw', $f) or die "write $f: $!";
    print $w $html; close $w;
}
print "done\n";
