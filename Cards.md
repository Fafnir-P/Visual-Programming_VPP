# Cards

The 209 launch cards of the Visual Programming Project, grouped into 8 categories. Each card has a name, a category, one sentence on what it does, and its ports. Ports are the places where a card takes data or a start signal in (inputs) or hands them on (outputs); cards are built by linking an output of one card to an input of another.

- Card numbers run in order through this file. They are working numbers and change when cards are added or removed.
- Each card sits in exactly one category. The "Group" column is a sub-theme inside the category.
- The ports come from the Python templates in `card_templates/` (the inputs and outputs of each card function). This file adds the class of each port. Both are kept in step by tests.
- Rules from the framework that shape these cards: the app runs locally for one owner on test data; connectors never call outside services; AI cards help at build time or take an answer a person brings in; triggers run only while the preview runs; loops live inside one card and are bounded.

## Port classes (colours)

Every port belongs to one class and is drawn in the colour of its class. **The colour says only what the port can be linked to. It says nothing about the data that flows through it.** Ports of the same colour can be linked; ports of different colours cannot. The emoji in the tables is a rough match; the app uses the exact colour in the Hex column.

| Colour | Class | Hex | Carries | An output of this class links to inputs of |
| --- | --- | --- | --- | --- |
| 🟩 green | **Text** (`text`) | `#2e9e5b` | Words and letters: names, e-mail, phone, prompts, file text, file names. | 🟩 Text, ⬜ Any |
| 🟦 blue | **Number** (`number`) | `#2f6fdd` | Whole and decimal numbers: amounts, counts, ids, percentages. | 🟦 Number, ⬜ Any |
| 🟨 yellow | **Yes/No** (`flag`) | `#e0b100` | One true or false answer. | 🟨 Yes/No, ⬜ Any |
| 🟧 orange | **Date/Time** (`date`) | `#ee7d1a` | A date, a time of day, or both. | 🟧 Date/Time, ⬜ Any |
| 🟪 purple | **Record** (`record`) | `#8f4fd0` | One set of named values: a saved record, a waiting item, an error, a rule, a setting. | 🟪 Record, ⬜ Any |
| 🟫 brown | **Record List** (`records`) | `#8a5a3c` | A list of records. | 🟫 Record List, ⬜ Any |
| 🩵 teal | **Value List** (`values`) | `#17a2b8` | A list of plain values: texts, numbers or ids. | 🩵 Value List, ⬜ Any |
| 🟥 red | **View** (`view`) | `#d9363e` | Something drawn on screen: a field, a table, a panel. | 🟥 View, ⬜ Any |
| ⬛ black (square) | **Control** (`control`) | `#2b2f36` | A signal that starts or orders work: it says only that a card should run, or has finished. It carries no data. | ⬛ Control, ⬜ Any |
| ⬜ grey (striped) | **Any** (`any`) | `#b0b7c3` | Wildcard: the data can be of any class. An Any output links to any input and an Any input accepts any output, so the app does not check the data; the builder must make sure it fits. | 🟩 Text, 🟦 Number, 🟨 Yes/No, 🟧 Date/Time, 🟪 Record, 🟫 Record List, 🩵 Value List, 🟥 View, ⬛ Control, ⬜ Any |

## Connection rules

The app checks these when a link is made. A link that breaks one is refused, a red message says why, and the reason is also written to the app's message list.

1. Both ends must be real: the cards and the ports must exist. (error code `no_such_port`)
2. A link goes from an output to an input. Two outputs, or two inputs, cannot be linked. (error code `direction`)
3. A card cannot be linked to itself. (error code `same_card`)
4. The classes must match: an output links only to an input of the same colour. The grey Any class works both ways (an Any output links to any input, and an Any input accepts any output) and is not type checked. There are no silent conversions (Number to Text, Record to Record List, and so on). (error code `type_mismatch`)
5. The same two ports cannot be linked twice. (error code `duplicate`)
6. An input takes one link. A source is replaced only by removing the old link first. An input marked + (such as `children+`) takes several links; every linked source is used, in the order the links were made. An output may feed any number of inputs; each input gets its own copy of the value. (error code `input_taken`)
7. Links may not form a loop. A card cannot, directly or through other cards, feed itself, because the order of work would then be undefined. Repeating work is done inside one card (for example Repeat For Each List Item). (error code `cycle`)

When a link is refused, nothing is created: the drag is cancelled and the canvas stays as it was. A red message names both ports, both classes and the rule that was broken. Both ports flash red, the reason is added to the message list (bottom right of the canvas) and is also written to the program's console, with the error code and the details. While you drag a link, the ports it could end on glow green, the others fade, and the line turns red over a port that would be refused.

Examples:

- **Allowed:** the 🟩 `value` output of Enter Text (Text) to the 🟩 `text` input of Trim Whitespace (Text): same colour.
- **Allowed:** the 🟫 `records` output of Filter Records By Condition to the 🟫 `records` input of Sort Records By Field: both Record List.
- **Allowed:** the 🟥 `view` output of Show Message Banner and the 🟥 `view` output of Show Status Badge, both to the 🟥 `children+` input of Arrange In Grid: an input marked + takes several links.
- **Refused (`type_mismatch`):** the 🟥 `view` output of Show Records Table to the 🟦 `value` input of Round Numeric Value: View is not Number.
- **Refused (`input_taken`):** a second link to the 🟦 `value` input of Round Numeric Value, which already has one.
- **Refused (`cycle`):** the 🟫 `records` output of Sort Records By Field back to the `records` input of the Filter Records By Condition that feeds it.

More about ports:

- An input marked ? is optional. An input with no mark must be linked, or given a value in the card's settings, before the project can be generated. When you press Generate, the app lists the open inputs (and a missing or unlinked App Start, or a missing App End), says where each one is, and asks you to confirm; you may still generate.
- Every card except triggers also has a black Start input and a black Done output (square ports, not repeated in the tables). Done of one card can feed Start of another to say which runs after which. A trigger card has no Start or Done. Its black `event` output (Control class) fires when the trigger fires: link it to the Start input of any card, or to the `steps+` or `branches+` input of a flow card, to begin work. The trigger's yes/no `fire` output is data and cannot be linked to a black Control port.
- Two special cards mark where a program begins and ends. App Start (Triggers / Orchestration) is on the canvas when the app opens; it cannot be deleted and only one is allowed. Its black `event` output starts the first card. App End takes several links into its black `finish` input, one from each card that ends a path. Neither has a Start or Done port. Run At App Start is a separate trigger that fires when the preview opens; use App Start as the beginning of the whole program.
- Record Lists, Value Lists and Views are separate classes, so a list cannot be linked where one record is expected. Use a card that turns one into the other (Find First Matching Record, Join Records Into List, Split Text By Separator).
- Settings that are typed into a card (a table name, a field name, a limit, a threshold) are not ports. Only data that comes from another card is a port.

How ports are written in the tables: the colour emoji, then the port name. `?` after an input means it is optional; `+` means it takes several links. A card with no listed ports has none besides the Start and Done ports.

## Categories

| Category | Cards | Numbers | What the cards share |
| --- | --- | --- | --- |
| UI / Interface | 34 | 001-034 | Cards the person using the app sees and touches: inputs, controls, layouts and displays. |
| Backend Processing | 68 | 035-102 | Cards that work on data while it moves through a flow, with no screen of their own. |
| Data Modeling / Storage | 31 | 103-133 | Cards that define the shape of records and read or write the app's saved data. |
| Logic / Validation | 22 | 134-155 | Cards that decide whether data or an action is acceptable, and which rule applies. |
| Triggers / Orchestration | 16 | 156-171 | Cards that start a flow or set the order in which steps run, only while the local preview runs. |
| Integrations / Connectors | 20 | 172-191 | Cards that prepare work for a person to do outside the app and take the result back; the app itself makes no outside call. |
| AI Capabilities | 10 | 192-201 | Cards where AI helps build the app or a person brings in an AI answer; the running app never calls AI. |
| Navigation / Output | 8 | 202-209 | Cards that move the user between screens and present or hand over final results. |
| **Total** | **209** | 001-209 | |

## UI / Interface (34 cards)

Cards the person using the app sees and touches: inputs, controls, layouts and displays.

| No. | Name | Category | Group | What it does | Inputs | Outputs |
| --- | --- | --- | --- | --- | --- | --- |
| 001 | Enter Text | UI / Interface | Form Inputs | Lets the user type a single line of text into a labeled field. | 🟩 value? | 🟥 view<br>🟩 value |
| 002 | Enter Paragraph | UI / Interface | Form Inputs | Lets the user type multiple lines of text into a labeled box. | 🟩 value? | 🟥 view<br>🟩 value |
| 003 | Enter Number | UI / Interface | Form Inputs | Lets the user type or adjust a numeric value with optional min and max. | 🟦 value? | 🟥 view<br>🟦 value |
| 004 | Pick Date | UI / Interface | Form Inputs | Lets the user select a date from a calendar popup. | 🟧 value? | 🟥 view<br>🟧 value |
| 005 | Pick Time | UI / Interface | Form Inputs | Lets the user select a time of day from hour and minute controls. | 🟧 value? | 🟥 view<br>🟧 value |
| 006 | Enter Email Address | UI / Interface | Form Inputs | Lets the user type an email address into a validated field. | 🟩 value? | 🟥 view<br>🟩 value |
| 007 | Enter Phone Number | UI / Interface | Form Inputs | Lets the user type a phone number into a formatted field. | 🟩 value? | 🟥 view<br>🟩 value |
| 008 | Enter Currency Amount | UI / Interface | Form Inputs | Lets the user type a monetary value with currency symbol and formatting. | 🟦 value? | 🟥 view<br>🟦 value |
| 009 | Pick Date Range | UI / Interface | Form Inputs | Lets the user choose a start date and an end date together from one calendar. | 🟧 start_date?<br>🟧 end_date? | 🟥 view<br>🟧 start_date<br>🟧 end_date |
| 010 | Choose From Dropdown | UI / Interface | Selection Controls | Lets the user pick one option from a collapsible list. | 🟩 value? | 🟥 view<br>🟩 value |
| 011 | Select Multiple Options | UI / Interface | Selection Controls | Lets the user check multiple items from a displayed list. | 🩵 value? | 🟥 view<br>🩵 value |
| 012 | Choose One Option | UI / Interface | Selection Controls | Lets the user select exactly one choice from visible radio buttons. | 🟩 value? | 🟥 view<br>🟩 value |
| 013 | Toggle Checkbox | UI / Interface | Selection Controls | Lets the user check or uncheck a single yes or no option. | 🟨 value? | 🟥 view<br>🟨 value |
| 014 | Pick From Searchable List | UI / Interface | Selection Controls | Lets the user type to narrow a long list and pick one entry. | 🟩 value? | 🟥 view<br>🟩 value |
| 015 | Rate With Stars | UI / Interface | Selection Controls | Lets the user choose a rating by clicking one to five stars. | 🟦 value? | 🟥 view<br>🟦 value |
| 016 | Arrange In Grid | UI / Interface | Layout Containers | Displays child cards in rows and columns with equal spacing. | 🟥 children+ | 🟥 view |
| 017 | Stack In Panel | UI / Interface | Layout Containers | Groups child cards vertically in a bordered section with optional title. | 🟥 children+ | 🟥 view |
| 018 | Organize In Tabs | UI / Interface | Layout Containers | Shows one group of cards at a time under clickable tab labels. | 🟫 tabs? | 🟥 view |
| 019 | Split Into Columns | UI / Interface | Layout Containers | Divides the space into side by side sections for child cards. | 🟥 children+ | 🟥 view |
| 020 | Collapse Section | UI / Interface | Layout Containers | Hides or shows child cards when the user clicks the section header. | 🟥 children+ | 🟥 view |
| 021 | Set App Title | UI / Interface | Layout Containers | Sets the name shown at the top of the app and in the window title. | none | 🟥 view |
| 022 | Show Records Table | UI / Interface | Data Display | Displays rows of data in sortable columns with optional pagination. | 🟫 records? | 🟥 view |
| 023 | List Records | UI / Interface | Data Display | Shows data items one per row with icon and text summary. | 🟫 records? | 🟥 view |
| 024 | Display Record Card | UI / Interface | Data Display | Presents a single record's fields in labeled rows or compact layout. | 🟪 record? | 🟥 view |
| 025 | Show Detail View | UI / Interface | Data Display | Displays all fields of one selected record in organized sections. | 🟪 record? | 🟥 view |
| 026 | Show Status Badge | UI / Interface | Data Display | Displays a colored label indicating state like pending approved or shipped. | 🟩 value? | 🟥 view |
| 027 | Display Barcode From Code | UI / Interface | Data Display | Shows a barcode image created from the product code or identifier of a record. | 🟩 value? | 🟥 view |
| 028 | Click Button | UI / Interface | Interactive Controls | Triggers an action when the user clicks the labeled button. | none | 🟥 view |
| 029 | Switch Toggle | UI / Interface | Interactive Controls | Lets the user turn a setting on or off with a sliding switch. | 🟨 value? | 🟥 view<br>🟨 value |
| 030 | Adjust Slider | UI / Interface | Interactive Controls | Lets the user pick a value by dragging a handle along a range. | 🟦 value? | 🟥 view<br>🟦 value |
| 031 | Choose File | UI / Interface | Interactive Controls | Lets the user browse and select a local file for upload or reading. | 🟩 filename? | 🟥 view<br>🟩 filename |
| 032 | Confirm Action | UI / Interface | Interactive Controls | Asks the user to approve or cancel before proceeding with an action. | none | 🟥 view |
| 033 | Show Message Banner | UI / Interface | Interactive Controls | Displays a dismissible notice with success warning or error styling. | 🟩 message | 🟥 view |
| 034 | Show Progress While Running | UI / Interface | Interactive Controls | Displays a progress bar or spinner during a long running step like importing data. | 🟦 current?<br>🟦 total? | 🟥 view |

## Backend Processing (68 cards)

Cards that work on data while it moves through a flow, with no screen of their own.

| No. | Name | Category | Group | What it does | Inputs | Outputs |
| --- | --- | --- | --- | --- | --- | --- |
| 035 | Convert Field Type | Backend Processing | Field Transformations | Changes a field from one data type to another, such as text to number or date to text. | 🟪 record | 🟪 record |
| 036 | Format Currency Value | Backend Processing | Field Transformations | Displays a number as currency with symbol, decimal places, and thousands separator. | 🟦 value | 🟩 text |
| 037 | Extract Substring | Backend Processing | Field Transformations | Pulls out a portion of text from a field using start position and length. | 🟩 text | 🟩 text |
| 038 | Combine Multiple Fields | Backend Processing | Field Transformations | Joins two or more fields into one with optional separator text between them. | 🟪 record | 🟩 text |
| 039 | Round Numeric Value | Backend Processing | Field Transformations | Rounds a number to a specified number of decimal places or to the nearest whole number. | 🟦 value | 🟦 value |
| 040 | Trim Whitespace | Backend Processing | Field Transformations | Removes leading and trailing spaces or line breaks from a text field. | 🟩 text | 🟩 text |
| 041 | Change Text Case | Backend Processing | Field Transformations | Converts text to uppercase, lowercase, or title case as specified. | 🟩 text | 🟩 text |
| 042 | Generate Unique Identifier | Backend Processing | Field Transformations | Creates a unique code for each new record from a prefix and a counter saved with the table. | 🟪 record | 🟪 record |
| 043 | Extract Domain From Email | Backend Processing | Field Transformations | Pulls the domain portion from an email address field for grouping or filtering. | 🟩 email | 🟩 domain |
| 044 | Format Phone Number | Backend Processing | Field Transformations | Standardizes phone numbers to a consistent display format with area code and separators. | 🟩 phone | 🟩 text |
| 045 | Filter Records By Condition | Backend Processing | List Operations | Keeps only the records in the current list that meet one or more conditions and drops the rest. | 🟫 records | 🟫 records |
| 046 | Sort Records By Field | Backend Processing | List Operations | Arranges the records in the current list in ascending or descending order of one or more fields. | 🟫 records | 🟫 records |
| 047 | Group Records By Value | Backend Processing | List Operations | Organizes records into named groups based on a shared field value or category. | 🟫 records | 🟫 groups |
| 048 | Remove Duplicate Records | Backend Processing | List Operations | Identifies and removes records with matching values in specified fields from the list. | 🟫 records | 🟫 records |
| 049 | Paginate Record List | Backend Processing | List Operations | Splits a list into fixed-size pages and returns one page at a time. | 🟫 records | 🟫 records<br>🟦 total<br>🟦 page<br>🟦 page_size<br>🟦 total_pages |
| 050 | Take Record Range | Backend Processing | List Operations | Returns part of a list of records, from a start position to an end position. | 🟫 records | 🟫 records |
| 051 | Find First Matching Record | Backend Processing | List Operations | Searches a list and returns the first record that meets the specified condition. | 🟫 records | 🟪 record<br>🟨 found |
| 052 | Flag Unusual Records | Backend Processing | List Operations | Marks records whose value falls outside a normal range the builder sets, such as far above the average. | 🟫 records | 🟫 records |
| 053 | Merge Two Lists | Backend Processing | List Operations | Combines two lists of records into one list, optionally dropping repeated records. | 🟫 list_a<br>🟫 list_b | 🟫 records |
| 054 | Pick Field From Records | Backend Processing | List Operations | Takes one named field out of every record and gives the values as a list, for example the ids of a list of records. | 🟫 records | 🩵 values |
| 055 | Filter Records By Date | Backend Processing | List Operations | Keeps the records whose date field is before, after or on a date that arrives while the app runs, such as today. | 🟫 records<br>🟧 compare_date | 🟫 records |
| 056 | Calculate Sum Of Field | Backend Processing | Calculations | Adds up numeric values from a specified field across all records in a list. | 🟫 records | 🟦 sum |
| 057 | Calculate Average Value | Backend Processing | Calculations | Computes the mean of numeric values from a field across a set of records. | 🟫 records | 🟦 average |
| 058 | Calculate Percentage Of Total | Backend Processing | Calculations | Divides a value by a sum and expresses the result as a percentage. | 🟦 value<br>🟦 total | 🟦 percentage |
| 059 | Find Smallest Or Largest Value | Backend Processing | Calculations | Finds the smallest or the largest number in a field across a list of records; a setting picks which. | 🟫 records | 🟦 value |
| 060 | Calculate Running Total | Backend Processing | Calculations | Adds each value to the sum of all previous values in sequence. | 🟫 records | 🟫 records |
| 061 | Calculate Stock Level | Backend Processing | Calculations | Computes current inventory by subtracting outgoing quantity from incoming quantity and starting balance. | 🟦 starting<br>🟦 incoming<br>🟦 outgoing | 🟦 stock |
| 062 | Count Records Matching Condition | Backend Processing | Calculations | Counts the records in the current list, or only those that meet a condition. | 🟫 records | 🟦 count |
| 063 | Calculate Reorder Quantity | Backend Processing | Calculations | Works out the next order amount from past usage with a plain formula, such as average use times lead time. | 🟦 average_use<br>🟦 lead_time | 🟦 quantity |
| 064 | Calculate From Two Values | Backend Processing | Calculations | Adds, subtracts, multiplies or divides two numbers, such as stock counted minus stock on record. | 🟦 first<br>🟦 second | 🟦 result |
| 065 | Change Value By Percent | Backend Processing | Calculations | Raises or lowers an amount by a percentage, for example to add tax or take off a discount. | 🟦 value | 🟦 result |
| 066 | Calculate Percentage Change | Backend Processing | Calculations | Shows how much a value rose or fell compared with an earlier value, as a percentage. | 🟦 old_value<br>🟦 new_value | 🟦 change |
| 067 | Compare Two Numbers | Backend Processing | Calculations | Answers yes or no to a comparison of two numbers, such as stock at or below the reorder level. | 🟦 first<br>🟦 second | 🟨 result |
| 068 | Split Text By Separator | Backend Processing | Text Processing | Splits text into separate values wherever a separator such as a comma, tab or vertical bar appears. | 🟩 text | 🩵 values |
| 069 | Search Text For Pattern | Backend Processing | Text Processing | Finds whether a text field contains a specified word, phrase, or pattern. | 🟩 text | 🟨 found<br>🟩 match |
| 070 | Replace Text In Field | Backend Processing | Text Processing | Substitutes all occurrences of specified text with replacement text in a field. | 🟩 text | 🟩 text |
| 071 | Split Text Into Lines | Backend Processing | Text Processing | Breaks multi-line text into separate strings, one per line, for individual processing. | 🟩 text | 🩵 lines |
| 072 | Fill Text Template | Backend Processing | Text Processing | Inserts field values into a template with placeholders to generate formatted text output. | 🟪 record | 🟩 text |
| 073 | Extract Number From Text | Backend Processing | Text Processing | Finds the first whole or decimal number in a text field and ignores the other characters. | 🟩 text | 🟦 number |
| 074 | Remove Special Characters | Backend Processing | Text Processing | Strips out non-alphanumeric characters from text, keeping only letters, numbers, and spaces. | 🟩 text | 🟩 text |
| 075 | Label Text By Keywords | Backend Processing | Text Processing | Gives each text record a label by matching keywords from a list the builder sets. | 🟪 record | 🟪 record |
| 076 | Calculate Date Difference | Backend Processing | Date and Time Operations | Computes the number of days, hours, or minutes between two dates or timestamps. | 🟧 start_date<br>🟧 end_date | 🟦 difference |
| 077 | Shift Date By Time | Backend Processing | Date and Time Operations | Moves a date forward or backward by a number of days, hours, or minutes; a setting picks the direction. | 🟧 date | 🟧 result |
| 078 | Compare Two Dates | Backend Processing | Date and Time Operations | Determines whether one date is before, after, or equal to another date. | 🟧 first_date<br>🟧 second_date | 🟩 comparison |
| 079 | Calculate Working Days | Backend Processing | Date and Time Operations | Counts weekdays between two dates, excluding weekends and optionally holidays. | 🟧 start_date<br>🟧 end_date | 🟦 working_days |
| 080 | Get Current Date And Time | Backend Processing | Date and Time Operations | Returns the present date and time when the card executes during preview. | none | 🟧 date<br>🟧 time<br>🟧 datetime |
| 081 | Merge Two Records | Backend Processing | Record Assembly | Combines fields from two records into one, with options for handling duplicate field names. | 🟪 record_a<br>🟪 record_b | 🟪 record |
| 082 | Build Record From Fields | Backend Processing | Record Assembly | Creates a new record by selecting and assembling individual field values. | none | 🟪 record |
| 083 | Rename Record Fields | Backend Processing | Record Assembly | Changes field names in a record to new names while keeping values unchanged. | 🟪 record | 🟪 record |
| 084 | Keep Only Selected Fields | Backend Processing | Record Assembly | Keeps only the named fields of a record and drops all the others. | 🟪 record | 🟪 record |
| 085 | Join Records Into List | Backend Processing | Record Assembly | Collects multiple individual records into a single list for batch processing. | 🟪 record_1<br>🟪 record_2 | 🟫 records |
| 086 | Build Summary Record | Backend Processing | Record Assembly | Puts up to four values under labels in one record and in label and value rows, ready for a summary table. | ⬜ value_1?<br>⬜ value_2?<br>⬜ value_3?<br>⬜ value_4? | 🟪 record<br>🟫 rows |
| 087 | Set Field Of Record | Backend Processing | Record Assembly | Gives a record one field with the value that arrives; without a record it makes a new one, ready for Update Existing Record. | ⬜ value<br>🟪 record? | 🟪 record |
| 088 | Route By Status Value | Backend Processing | Conditional Routing | Sends a record to the output for its status value; records with any other status go to a no-match output. | 🟪 record | 🟪 pending<br>🟪 shipped<br>🟪 delivered<br>🟪 no_match |
| 089 | Route By Numeric Range | Backend Processing | Conditional Routing | Sends a record to the output whose number range it falls in; records outside every range go to a no-match output. | 🟪 record | 🟪 low<br>🟪 medium<br>🟪 high<br>🟪 no_match |
| 090 | Route By Text Match | Backend Processing | Conditional Routing | Sends a record to an output when a text field matches a chosen value; other records go to a no-match output. | 🟪 record | 🟪 match<br>🟪 no_match |
| 091 | Route By Field Presence | Backend Processing | Conditional Routing | Sends a record one way if a field has a value and another way if it is empty. | 🟪 record | 🟪 has_value<br>🟪 is_empty |
| 092 | Route By Date Comparison | Backend Processing | Conditional Routing | Sends a record to an output depending on whether a date is in the past, today or in the future. | 🟪 record | 🟪 past<br>🟪 today<br>🟪 future |
| 093 | Route By Category | Backend Processing | Conditional Routing | Sends a record to the output for its category or type; records with an unlisted category go to a no-match output. | 🟪 record | 🟪 hardware<br>🟪 tools<br>🟪 supplies<br>🟪 no_match |
| 094 | Route By List Membership | Backend Processing | Conditional Routing | Sends a record one way if a field value appears in a reference list and another way if it does not. | 🟪 record | 🟪 in_list<br>🟪 not_in_list |
| 095 | Branch On Yes/No | Backend Processing | Conditional Routing | Sends the value out of the yes port when the answer is yes and out of the no port when it is no. | 🟨 condition<br>⬜ value? | ⬜ yes<br>⬜ no |
| 096 | Handle Error Without Stopping | Backend Processing | Error Handling | Catches a failure in a step so the rest of the flow can carry on along an error path. | ⬜ value | 🟨 ok<br>⬜ value<br>🟪 error |
| 097 | Set Default Value On Error | Backend Processing | Error Handling | Provides a fallback value when a field calculation or transformation fails. | ⬜ value | ⬜ value |
| 098 | Retry Failed Step | Backend Processing | Error Handling | Runs a failed local step again a set number of times, only if it is safe to repeat, then follows the error path. | ⬛ step | 🟨 success<br>⬜ result<br>🟦 attempts<br>🟪 error |
| 099 | Log Error Details | Backend Processing | Error Handling | Records information about a failure for review without stopping the application flow. | 🟪 error | 🟨 logged<br>🟩 event_kind |
| 100 | Flag Record With Error | Backend Processing | Error Handling | Marks a record as having encountered a problem and continues processing remaining records. | 🟪 record | 🟪 record |
| 101 | Skip Invalid Record | Backend Processing | Error Handling | Removes a record from further processing when it fails validation or transformation. | 🟪 record | 🟪 record<br>🟨 skipped |
| 102 | Collect Error Records | Backend Processing | Error Handling | Gathers all records that encountered errors into a separate list for review. | 🟫 records | 🟫 errors<br>🟫 valid |

## Data Modeling / Storage (31 cards)

Cards that define the shape of records and read or write the app's saved data.

| No. | Name | Category | Group | What it does | Inputs | Outputs |
| --- | --- | --- | --- | --- | --- | --- |
| 103 | Define Data Table | Data Modeling / Storage | Schema Definition | Creates a new table with a name and description to hold records in the app. | none | 🟩 table_name |
| 104 | Add Field To Table | Data Modeling / Storage | Schema Definition | Adds a named column to a table with a data type, and optional simple rules such as required or a number range. | none | 🟩 field_name |
| 105 | Set Field Default Value | Data Modeling / Storage | Schema Definition | Assigns a default value that fills automatically when creating a new record in the table. | ⬜ default_value | 🟩 field_name |
| 106 | Link Tables By Relationship | Data Modeling / Storage | Schema Definition | Connects two tables so records in one can reference records in the other. | none | 🟩 field_name |
| 107 | Define Choice List | Data Modeling / Storage | Schema Definition | Creates a dropdown list of allowed values that a field can use across the app. | 🩵 choices | 🟩 field_name |
| 108 | Add Calculated Field | Data Modeling / Storage | Schema Definition | Defines a field whose value is worked out from other fields in the same record, using a formula the builder sets. | none | 🟩 field_name |
| 109 | Enable Change History Tracking | Data Modeling / Storage | Schema Definition | Makes a table keep the last few versions of each record, with when each change was made. | none | 🟩 table_name |
| 110 | Define App Settings | Data Modeling / Storage | Schema Definition | Keeps the owner's app-wide options, such as default currency or reorder level, in one saved settings record. | 🟪 settings | 🟪 record |
| 111 | Create New Record | Data Modeling / Storage | Record Operations | Adds a single record to a table with values the user provides or maps from inputs. | 🟪 values | 🟪 record |
| 112 | Read Record By ID | Data Modeling / Storage | Record Operations | Retrieves one record from a table using its unique identifier. | 🟦 id | 🟪 record |
| 113 | Update Existing Record | Data Modeling / Storage | Record Operations | Changes field values in a record the user selects or identifies. | 🟦 id<br>🟪 changes | 🟪 record |
| 114 | Delete Record | Data Modeling / Storage | Record Operations | Removes a record from the table permanently or marks it as deleted if protected. | 🟦 id | 🟪 record |
| 115 | Create Multiple Records | Data Modeling / Storage | Record Operations | Adds several records to a table at once from a list or imported data. | 🟫 records | 🟫 records<br>🟦 count |
| 116 | Create Or Update Record | Data Modeling / Storage | Record Operations | Creates a record if no saved record has the same key value, or updates that record if one does. | 🟪 values | 🟪 record<br>🟨 created |
| 117 | Archive Or Restore Record | Data Modeling / Storage | Record Operations | Moves a record to inactive status without deleting it, or returns an archived record to active status; a setting picks which. | 🟦 id | 🟪 record |
| 118 | Copy Record | Data Modeling / Storage | Record Operations | Creates a new record by copying an existing one, so the user can change a few fields. | 🟦 id | 🟪 record |
| 119 | Update Field Across Records | Data Modeling / Storage | Record Operations | Changes one field to a new value in several selected or filtered records at once. | 🩵 ids<br>🟩 field<br>⬜ value | 🟦 count |
| 120 | Delete Multiple Records | Data Modeling / Storage | Record Operations | Removes several selected or filtered records at once after a confirmation. | 🩵 ids | 🟦 count |
| 121 | Restore Previous Record Version | Data Modeling / Storage | Record Operations | Puts a record back to an earlier kept version, such as how it was before its last saved change. | 🟦 id | 🟪 record |
| 122 | Query Saved Records By Criteria | Data Modeling / Storage | Query Building | Reads the saved records of a table that match one or more conditions, joined with AND or OR. | 🟪 where | 🟫 records<br>🟦 count |
| 123 | Join Related Tables | Data Modeling / Storage | Query Building | Combines records from two related tables into one result set for display or export. | 🟫 left_records | 🟫 records<br>🟦 count |
| 124 | Search Saved Records By Text | Data Modeling / Storage | Query Building | Finds saved records where any text field contains the words or phrase the user enters. | 🟩 query | 🟫 records<br>🟦 count |
| 125 | Group And Summarize Saved Data | Data Modeling / Storage | Query Building | Groups saved records by a field and calculates totals, averages or counts for each group. | none | 🟫 groups<br>🟦 count |
| 126 | Set Primary Key Field | Data Modeling / Storage | Keys and Constraints | Designates a field as the unique identifier that every record must have. | none | 🟩 field_name |
| 127 | Enforce Unique Field Value | Data Modeling / Storage | Keys and Constraints | Makes the saved table itself refuse two records with the same value in the specified field. | none | 🟩 field_name |
| 128 | Reference Linked Record | Data Modeling / Storage | Keys and Constraints | Makes sure a field value points to a record that exists in the linked table. | 🟪 record | 🟪 record |
| 129 | Prevent Accidental Delete | Data Modeling / Storage | Keys and Constraints | Blocks deletion of a record if other records reference it or a condition is met. | 🟦 record_id | 🟨 can_delete |
| 130 | Import Records | Data Modeling / Storage | Import and Export | Loads records into a table from a CSV or JSON file the user selects; files that are too large are refused. | 🟩 content | 🟦 count<br>🟫 records |
| 131 | Export Table | Data Modeling / Storage | Import and Export | Saves a whole table, the records matching a filter, or the records on screen to a CSV or JSON file the user picks. | 🟫 records? | 🟩 filename<br>🟩 mime<br>🟩 content |
| 132 | Load Sample Data Set | Data Modeling / Storage | Import and Export | Fills a table with example records so the user can test the app immediately. | 🟫 sample_data? | 🟦 count<br>🟫 records |
| 133 | Read Chosen File | Data Modeling / Storage | Import and Export | Passes on the text of the file the user chose, after checking its name, type and size. | 🟩 filename<br>🟩 content | 🟩 content<br>🟩 filename<br>🟦 size |

## Logic / Validation (22 cards)

Cards that decide whether data or an action is acceptable, and which rule applies.

| No. | Name | Category | Group | What it does | Inputs | Outputs |
| --- | --- | --- | --- | --- | --- | --- |
| 134 | Check Field Is Required | Logic / Validation | Field Validation | Stops the user if a mandatory field is left empty before saving or submitting. | ⬜ value | ⬜ value |
| 135 | Validate Field Type | Logic / Validation | Field Validation | Confirms a field contains the correct data type such as number, text, or date. | ⬜ value | ⬜ value |
| 136 | Match Format Pattern | Logic / Validation | Field Validation | Checks a field against a pattern like email address, phone number, or code format. | ⬜ value | ⬜ value |
| 137 | Validate Number Range | Logic / Validation | Field Validation | Ensures a numeric field falls between a minimum and maximum value. | 🟦 value | 🟦 value |
| 138 | Check Text Length | Logic / Validation | Field Validation | Verifies a text field meets minimum or maximum character count limits. | 🟩 value | 🟩 value |
| 139 | Validate Against Allowed List | Logic / Validation | Field Validation | Confirms a field value exists in a predefined list of acceptable options. | ⬜ value | ⬜ value |
| 140 | Reject Future Date | Logic / Validation | Field Validation | Prevents a date field from being set to a date beyond today. | 🟧 value | 🟧 value |
| 141 | Compare Two Fields | Logic / Validation | Cross-Field Rules | Checks whether two fields meet a condition like greater than, equal to, or not matching. | 🟪 value | 🟪 value |
| 142 | Verify Sum Equals Total | Logic / Validation | Cross-Field Rules | Confirms that line item amounts add up to a specified total field. | 🟪 value | 🟪 value |
| 143 | Require Either Or Field | Logic / Validation | Cross-Field Rules | Ensures at least one of two fields is filled, but not necessarily both. | 🟪 value | 🟪 value |
| 144 | Require Dependent Field | Logic / Validation | Cross-Field Rules | Makes a second field mandatory, and marks it required on screen, only when a first field has a certain value. | 🟪 value | 🟪 value<br>🟨 field_required |
| 145 | Validate Date Order | Logic / Validation | Cross-Field Rules | Confirms a start date comes before an end date or ship date follows order date. | 🟪 value | 🟪 value |
| 146 | Prevent Negative Stock | Logic / Validation | Business Rules | Blocks inventory updates that would result in stock quantity falling below zero. | 🟪 record | 🟪 record |
| 147 | Flag Reorder Level Reached | Logic / Validation | Business Rules | Signals when inventory quantity drops to or below the reorder threshold. | 🟪 record | 🟪 record<br>🟨 flag<br>🟩 reason |
| 148 | Require Approval Above Amount | Logic / Validation | Business Rules | Marks an order or transaction for manual approval if value exceeds a set limit. | 🟪 record | 🟪 record<br>🟨 requires_approval<br>🟩 reason |
| 149 | Prevent Duplicate Order | Logic / Validation | Business Rules | Prevents creating a new order when one with the same key details, such as customer, item and date, already exists. | 🟪 record | 🟪 record |
| 150 | Enforce Lead Time Limit | Logic / Validation | Business Rules | Ensures a delivery or completion date allows enough days from the order date. | 🟪 record | 🟪 record |
| 151 | Check Valid Status Transition | Logic / Validation | Business Rules | Confirms a status change follows allowed steps like pending to shipped to delivered. | 🟪 record | 🟪 record |
| 152 | Show Or Hide Field | Logic / Validation | Conditional Display Rules | Decides whether a field appears on screen based on another field or record state. | 🟪 record | 🟪 record<br>🟨 visible |
| 153 | Enable Or Disable Field | Logic / Validation | Conditional Display Rules | Controls whether a field can be edited depending on conditions like record status. | 🟪 record | 🟪 record<br>🟨 enabled |
| 154 | Confirm Destructive Action | Logic / Validation | Safety Checks | Asks the user to confirm before a high-impact step, such as deleting several records. | 🟨 confirmed | 🟨 proceed |
| 155 | Stop On Error Threshold | Logic / Validation | Safety Checks | Halts processing when the count of validation or import errors exceeds a set limit. | 🟫 errors | 🟨 proceed<br>🟨 stopped |

## Triggers / Orchestration (16 cards)

Cards that start a flow or set the order in which steps run, only while the local preview runs.

| No. | Name | Category | Group | What it does | Inputs | Outputs |
| --- | --- | --- | --- | --- | --- | --- |
| 156 | App Start | Triggers / Orchestration | Start and End | The one place every flow of the app begins: its event output starts the first cards when the app starts. | none | ⬛ event<br>🟧 started_at |
| 157 | App End | Triggers / Orchestration | Start and End | Marks a place where the app finishes; when a flow reaches it, the finish is written to the event log. | ⬛ finish+ | none |
| 158 | Run When Button Pressed | Triggers / Orchestration | User Action Triggers | Starts a flow when the user clicks a button in the application interface. | 🟨 pressed | 🟨 fire<br>⬛ event |
| 159 | Run When Form Submitted | Triggers / Orchestration | User Action Triggers | Starts a flow when the user submits a form with input values. | 🟨 submitted<br>🟪 values | 🟨 fire<br>⬛ event |
| 160 | Run When Page Opened | Triggers / Orchestration | User Action Triggers | Starts a flow when the user navigates to a specific page in the application. | 🟨 opened | 🟨 fire<br>⬛ event |
| 161 | Run When Record Selected | Triggers / Orchestration | User Action Triggers | Starts a flow when the user chooses a record from a list or table. | 🟨 selected<br>🟪 record | 🟨 fire<br>⬛ event |
| 162 | Run On A Timer | Triggers / Orchestration | Timer Triggers | Runs a flow once after a delay, or again and again at a fixed interval, only while the app preview is running. | none | 🟨 fire<br>⬛ event<br>🟧 next_due |
| 163 | Run At App Start | Triggers / Orchestration | Timer Triggers | Runs a flow automatically when the app preview begins running. | 🟨 started | 🟨 fire<br>⬛ event |
| 164 | Run When Record Created | Triggers / Orchestration | Data Event Triggers | Starts a flow when a new record is added while the app preview is running. | 🟩 table | 🟨 fire<br>⬛ event<br>🟪 record<br>🟦 last_seen_id |
| 165 | Run When Record Changed | Triggers / Orchestration | Data Event Triggers | Starts a flow when an existing record is updated while the app preview is running. | 🟩 table | 🟨 fire<br>⬛ event<br>🟪 record<br>🟪 before<br>🟪 after |
| 166 | Run When Record Deleted | Triggers / Orchestration | Data Event Triggers | Starts a flow when a record is removed while the app preview is running. | 🟩 table | 🟨 fire<br>⬛ event<br>🟪 record |
| 167 | Run When Value Crosses Threshold | Triggers / Orchestration | Data Event Triggers | Starts a flow when a numeric field goes above or below a limit while the app preview is running. | 🟩 table<br>🟦 record_id | 🟨 fire<br>⬛ event<br>🟦 value<br>🟩 crossed |
| 168 | Run Steps In Sequence | Triggers / Orchestration | Flow Control | Runs the connected steps one after another, in the order the user set. | ⬛ steps+ | ⬜ results |
| 169 | Wait For All Steps To Complete | Triggers / Orchestration | Flow Control | Waits until every branch the flow actually took has finished, then carries on. | ⬛ branches+ | ⬜ results<br>🟨 all_done |
| 170 | Wait For Condition With Timeout | Triggers / Orchestration | Flow Control | Pauses until a condition becomes true or the required time limit runs out, whichever comes first. | 🟨 condition<br>🟦 elapsed? | 🟨 ready<br>🟨 timeout<br>🟨 wait_more |
| 171 | Repeat For Each List Item | Triggers / Orchestration | Flow Control | Runs the connected steps once for each record in a list, up to a limit set when building. | 🟫 items<br>⬛ step | ⬜ results<br>🟦 count |

## Integrations / Connectors (20 cards)

Cards that prepare work for a person to do outside the app and take the result back; the app itself makes no outside call.

| No. | Name | Category | Group | What it does | Inputs | Outputs |
| --- | --- | --- | --- | --- | --- | --- |
| 172 | Build Order Request | Integrations / Connectors | Payload Preparation | Formats order data into a structured request ready for a person to submit to a supplier. | 🟪 order | 🟪 payload<br>🟩 instructions |
| 173 | Build Shipment Notice | Integrations / Connectors | Payload Preparation | Formats shipment details into a notice ready for a person to send to a recipient. | 🟪 shipment | 🟪 payload<br>🟩 instructions |
| 174 | Build Supplier Message | Integrations / Connectors | Payload Preparation | Formats supplier communication data into a message ready for a person to send. | 🟪 message | 🟪 payload<br>🟩 instructions |
| 175 | Build Spreadsheet Export | Integrations / Connectors | Payload Preparation | Formats records into a table ready for a person to paste into a spreadsheet. | 🟫 records | 🟪 payload<br>🟩 instructions |
| 176 | Build Email Text | Integrations / Connectors | Payload Preparation | Formats data into email-ready text ready for a person to copy and send. | 🟪 data | 🟪 payload<br>🟩 instructions |
| 177 | Build Data File | Integrations / Connectors | Payload Preparation | Formats records into a file ready for a person to upload to another tool. | 🟫 records | 🟪 payload<br>🟩 instructions |
| 178 | Show Manual Steps | Integrations / Connectors | Human Instructions | Displays step-by-step instructions for a person to follow outside the app. | 🩵 steps | 🟥 view |
| 179 | Show Copyable Text | Integrations / Connectors | Human Instructions | Displays text in a copyable block for a person to paste elsewhere. | 🟩 text | 🟥 view |
| 180 | Show Action Checklist | Integrations / Connectors | Human Instructions | Displays a checklist of tasks for a person to complete outside the app. | 🩵 items | 🟥 view |
| 181 | Show Waiting Item | Integrations / Connectors | Human Instructions | Displays an item paused until a person completes an outside action. | 🟪 item | 🟥 view |
| 182 | Show Pending Reminder | Integrations / Connectors | Human Instructions | Displays a reminder of actions still waiting for a person to complete outside. | 🟫 items | 🟥 view |
| 183 | Enter Outside Result | Integrations / Connectors | Result Intake | Shows a form where a person types the result of an outside action, such as a reference number or confirmed quantity. | 🟪 item | 🟥 view<br>⬜ value |
| 184 | Import Result File | Integrations / Connectors | Result Intake | Lets a person pick and import a result file from an outside action. | 🟪 item | 🟥 view<br>🟩 content<br>🟩 filename |
| 185 | Match Result To Item | Integrations / Connectors | Result Intake | Matches a result entered by a person to the waiting item that triggered it. | 🟪 result<br>🟫 items | 🟪 matched_item<br>🟪 result |
| 186 | Reject Invalid Result | Integrations / Connectors | Result Intake | Rejects a result entered by a person if it is stale or does not match. | 🟪 result<br>🟪 item | 🟨 valid<br>🟩 reason |
| 187 | Reconcile Stale Result | Integrations / Connectors | Result Intake | Shows what changed in a record since an outside action began, and lets the user accept or discard the result. | 🟪 result<br>🟪 old_item<br>🟪 current_item | 🟥 view<br>🟩 action |
| 188 | Resume After Result | Integrations / Connectors | Local Continuation | Continues the flow after a person enters a result from an outside action. | 🟪 result<br>🟪 item | 🟨 resumed<br>🟪 data |
| 189 | Mark Item Outcome | Integrations / Connectors | Local Continuation | Marks an item as done or failed based on the result a person entered. | 🟪 item<br>🟪 result | 🟪 item |
| 190 | Log Outside Action | Integrations / Connectors | Local Continuation | Records a history entry when a person completes an outside action. | 🟪 item<br>🟪 result | 🟨 logged |
| 191 | Show Still Pending | Integrations / Connectors | Local Continuation | Displays items still waiting for a person to complete outside actions. | 🟫 items | 🟫 pending_items<br>🟦 count |

## AI Capabilities (10 cards)

Cards where AI helps build the app or a person brings in an AI answer; the running app never calls AI.

| No. | Name | Category | Group | What it does | Inputs | Outputs |
| --- | --- | --- | --- | --- | --- | --- |
| 192 | Suggest Record Layout | AI Capabilities | Build-Time Assistance | Proposes field names and types for a new record table at build time based on the app description. | 🟪 proposal | 🟪 schema |
| 193 | Draft Sample Records | AI Capabilities | Build-Time Assistance | Generates example rows for testing at build time using the defined record structure. | 🟪 proposal | 🟫 records |
| 194 | Propose Field Mappings | AI Capabilities | Build-Time Assistance | Suggests how imported columns match record fields at build time by comparing names and types. | 🟪 proposal | 🟪 mappings |
| 195 | Draft Validation Rules | AI Capabilities | Build-Time Assistance | Creates initial field validation logic at build time from field names and intended data types. | 🟪 proposal | 🟫 rules |
| 196 | Draft Acceptance Checklist | AI Capabilities | Build-Time Assistance | Proposes, at build time, a checklist of things to try in the finished app, based on the cards used. | 🟪 proposal | 🩵 checklist |
| 197 | Explain App In Plain Words | AI Capabilities | Build-Time Assistance | Writes, at build time, a short plain-language description of how the connected cards work together. | 🟪 proposal | 🟩 explanation |
| 198 | Draft Field Help Text | AI Capabilities | Build-Time Assistance | Writes, at build time, short help text for each input field from its name and type. | 🟪 proposal | 🟪 help |
| 199 | Prepare AI Prompt | AI Capabilities | Human-AI Loop | Formats the fields the user picks into a question to copy into an outside AI tool, within a length limit. | 🟪 record | 🟩 prompt<br>🟪 context |
| 200 | Accept AI Answer | AI Capabilities | Human-AI Loop | Receives text the user supplies from an AI tool and stores it in the specified format. | 🟩 text | ⬜ answer<br>🟩 format |
| 201 | Check Answer Shape | AI Capabilities | Human-AI Loop | Checks, with simple rules, that the answer the user supplies from an AI tool has the expected format and structure before use. | ⬜ answer | ⬜ value<br>🟨 valid |

## Navigation / Output (8 cards)

Cards that move the user between screens and present or hand over final results.

| No. | Name | Category | Group | What it does | Inputs | Outputs |
| --- | --- | --- | --- | --- | --- | --- |
| 202 | Open Detail Screen | Navigation / Output | Screen Navigation | Displays the full record view when the user selects an item from a list. | 🟪 record? | 🟥 view |
| 203 | Go Back To List | Navigation / Output | Screen Navigation | Returns the user to the previous list or overview screen. | none | 🟥 view |
| 204 | Open Pop-Up Panel | Navigation / Output | Screen Navigation | Shows a temporary overlay window for quick edits or details without leaving the current screen. | 🟥 content? | 🟥 view |
| 205 | Summary Table | Navigation / Output | Reports | Presents key totals and counts in a table layout for quick overview. | 🟫 data | 🟥 view |
| 206 | Chart Over Time | Navigation / Output | Reports | Displays a line or bar chart showing how a measure changes across dates or periods. | 🟫 data | 🟥 view |
| 207 | Grouped Totals View | Navigation / Output | Reports | Shows aggregated counts or sums organized by category or location. | 🟫 data | 🟥 view |
| 208 | Exception List | Navigation / Output | Reports | Lists low-stock, overdue or out-of-limit records that need attention. | 🟫 records | 🟥 view |
| 209 | Print-Friendly Page | Navigation / Output | Export and Print | Formats the current view for clean printing, without menus or navigation elements. | 🟥 content? | 🟥 view |

## Where the ideas came from

The categories and groups follow how common low-code and workflow tools split their building blocks, fitted to the framework (Python apps, local single-owner preview, no live outside calls). Sources read:

- [Retool components](https://retool.com/use-case/react-components-library)
- [n8n workflow nodes](https://blog.n8n.io/ai-agentic-workflows/)
- [Node-RED core nodes](https://nodered.org/docs/user-guide/nodes)
- [Appsmith widgets](https://www.appsmith.com/widgets)
- [Budibase components](https://docs.budibase.com/docs/components)
- [Streamlit widgets](https://docs.streamlit.io/develop/api-reference/widgets)
- [Django admin create, read, update, delete](https://www.geeksforgeeks.org/python/crud-operations-in-django-admin/)
- [Zapier workflows](https://zapier.com/workflows)
- [AI workflow patterns in n8n](https://osher.com.au/blog/how-to-build-ai-workflow-n8n/)

Content was rephrased and fitted to this project; no text was copied from these pages.
