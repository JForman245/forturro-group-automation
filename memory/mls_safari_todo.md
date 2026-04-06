# MLS Safari Print-to-PDF — Must fix by 7 AM April 4

## Problem
Safari login via AppleScript/JS not working — Vue form doesn't pick up programmatic input.

## What works
- Playwright headless: login, search, find listing, generate PDF via CDP (453KB, formatting ~7/10)
- AppleScript: Cmd+P, PDF > Save as PDF dialog navigation (confirmed working on test page)
- MLSHelper.app has Accessibility permissions
- Safari has Allow Remote Automation + Allow JavaScript from Apple Events enabled

## What doesn't work
- Safari + Selenium: driver.quit() closes the window, can't hand off to AppleScript
- Safari JS do JavaScript: Vue form doesn't react to .value changes or native setter trick
- Safari AppleScript keystrokes: may be landing in address bar not form fields
- SafariDriver blocks window.print() and File > Print in automation mode

## Solution path
1. Use Playwright (not Selenium) with headed Chromium to login + navigate to listing
2. OR: Use AppleScript to open Safari, navigate to login URL, use TAB key to navigate to form fields (not JS focus), type credentials, submit
3. Once on listing page, use Cmd+P → handle print dialog with AppleScript
4. Key: the print dialog is the CLASSIC macOS dialog (not modern Safari preview) because Jeff has a Brother printer configured

## Jeff's exact workflow (from video analysis)
1. Safari already logged in → navigate to Paragon
2. Power Search → type address → click ACTIVE listing
3. All Fields Detail loads (the default view)
4. Cmd+P → classic macOS print dialog (shows Brother HL-L2320D)
5. Click PDF dropdown (bottom-left) → Save as PDF...
6. Type address as filename → Desktop → Save
7. Result: multi-page PDF with perfect formatting

## Deadline
Jeff has showings at 9 AM April 4 — needs this working by 7 AM.
