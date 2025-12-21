#!/bin/bash
# Script to wake macOS for scheduled email processing
#
# Schedule:
# - 7:58 AM Monday-Friday for daily digests (wake 2 min before 8am agent start)
# - 7:57 AM Sunday for weekly deep dives (wake 3 min before 8am agent start)
#
# To install this wake schedule, run:
#   sudo pmset repeat wakeorpoweron MTWRF 07:58:00 wakeorpoweron U 07:57:00
#
# To verify the schedule:
#   pmset -g sched
#
# To clear the schedule:
#   sudo pmset repeat cancel

echo "macOS Wake Schedule for Email Agent"
echo "===================================="
echo ""
echo "Required wake times:"
echo "  - Monday-Friday: 7:58 AM (for daily digest at 8:00 AM)"
echo "  - Sunday: 7:57 AM (for weekly deep dives at 8:00 AM)"
echo ""
echo "To install, run:"
echo "  sudo pmset repeat wakeorpoweron MTWRF 07:58:00 wakeorpoweron U 07:57:00"
echo ""
echo "Current schedule:"
pmset -g sched
