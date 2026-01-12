"""
Generate Sample Insurance PDFs for RAGMesh Testing

This script creates realistic insurance policy documents for testing
the RAGMesh system. It generates PDFs with proper formatting, metadata,
and insurance-specific content.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from datetime import datetime
import os

# Sample insurance documents content
SAMPLE_DOCUMENTS = [
    {
        "filename": "homeowners_policy_HO3_california.pdf",
        "form_number": "HO-3",
        "doc_type": "policy",
        "state": "CA",
        "effective_date": "2024-01-01",
        "title": "Homeowners Insurance Policy - Form HO-3",
        "content": [
            {
                "heading": "POLICY DECLARATIONS",
                "text": """
                Form Number: HO-3
                Policy Number: CA-HO-2024-001234
                Named Insured: John Doe
                Mailing Address: 123 Main Street, Los Angeles, CA 90001
                Policy Period: January 1, 2024 to January 1, 2025
                State: California

                This policy provides coverage for your dwelling, personal property, and liability
                as detailed in the following sections. This is a Special Form (HO-3) policy
                providing open perils coverage for your dwelling and named perils for personal property.
                """
            },
            {
                "heading": "SECTION I - PROPERTY COVERAGES",
                "text": """
                Coverage A - Dwelling: $500,000
                We cover the dwelling on the residence premises shown in the Declarations, including
                structures attached to the dwelling. We also cover building materials and supplies
                located on or next to the residence premises used to construct, alter or repair
                the dwelling or other structures on the residence premises.

                Coverage B - Other Structures: $50,000 (10% of Coverage A)
                We cover other structures on the residence premises separated from the dwelling
                by clear space. This includes structures connected to the dwelling by only a fence,
                utility line, or similar connection. Coverage B does not apply to land.

                Coverage C - Personal Property: $350,000 (70% of Coverage A)
                We cover personal property owned or used by an insured while it is anywhere in
                the world. After a loss and at your request, we will cover personal property
                owned by others while the property is on the part of the residence premises
                occupied by an insured. Special limits apply to certain types of property.

                Coverage D - Loss of Use: $150,000 (30% of Coverage A)
                If a loss covered under Section I makes the residence premises not fit to live in,
                we cover the Additional Living Expense necessary to maintain your normal standard
                of living. We also cover the Fair Rental Value of that part of the residence
                premises rented to others or held for rental by you.
                """
            },
            {
                "heading": "SECTION I - PERILS INSURED AGAINST",
                "text": """
                Coverage A - Dwelling and Coverage B - Other Structures
                We insure against risks of direct physical loss to property described in Coverages A
                and B, except losses excluded under Section I - Exclusions.

                Coverage C - Personal Property
                We insure for direct physical loss to the property described in Coverage C caused
                by the following perils:

                1. Fire or Lightning
                2. Windstorm or Hail
                3. Explosion
                4. Riot or Civil Commotion
                5. Aircraft
                6. Vehicles
                7. Smoke
                8. Vandalism or Malicious Mischief
                9. Theft
                10. Falling Objects
                11. Weight of Ice, Snow or Sleet
                12. Accidental Discharge or Overflow of Water or Steam
                13. Sudden and Accidental Tearing Apart, Cracking, Burning or Bulging
                14. Freezing
                15. Sudden and Accidental Damage from Artificially Generated Electrical Current
                16. Volcanic Eruption
                """
            },
            {
                "heading": "SECTION I - EXCLUSIONS",
                "text": """
                We do not insure for loss caused directly or indirectly by any of the following.
                Such loss is excluded regardless of any other cause or event contributing
                concurrently or in any sequence to the loss:

                1. Ordinance or Law
                Ordinance or Law means any ordinance or law requiring or regulating the construction,
                demolition, remodeling, renovation or repair of property, including removal of
                any resulting debris. This Exclusion does not apply to the amount of coverage
                provided under Additional Coverage - Ordinance or Law.

                2. Earth Movement
                Earth Movement means earthquake, landslide, mudflow, earth sinking, rising or
                shifting. This exclusion applies regardless of whether the earth movement is
                combined with water, whether natural or from any other source. Earth movement
                resulting from explosion, fire, breakage of water or sewer lines, or theft
                is covered.

                3. Water Damage
                Water Damage means flood, surface water, waves, tidal water, overflow of a body
                of water, or spray from any of these, whether or not driven by wind. Water
                damage does not include water which backs up through sewers or drains or which
                overflows or is discharged from a sump, sump pump or related equipment.

                4. Neglect
                Neglect means neglect of an insured to use all reasonable means to save and
                preserve property at and after the time of a loss.

                5. War
                War including undeclared war, civil war, insurrection, rebellion, revolution,
                or acts furthering any of these, including action hindering or defending against
                an actual or expected attack by government, sovereign or other authority using
                military personnel or other agents.
                """
            },
            {
                "heading": "SECTION II - LIABILITY COVERAGES",
                "text": """
                Coverage E - Personal Liability: $300,000 per occurrence
                If a claim is made or a suit is brought against an insured for damages because
                of bodily injury or property damage caused by an occurrence to which this coverage
                applies, we will pay up to our limit of liability for the damages for which an
                insured is legally liable.

                Coverage F - Medical Payments to Others: $5,000 per person
                We will pay the necessary medical expenses that are incurred or medically
                ascertained within three years from the date of an accident causing bodily injury.
                Medical expenses means reasonable charges for medical, surgical, x-ray, dental,
                ambulance, hospital, professional nursing, prosthetic devices and funeral services.
                """
            },
            {
                "heading": "CONDITIONS",
                "text": """
                Section I and II - Conditions apply to all coverages under this policy.

                Your Duties After Loss
                In case of a loss to which this insurance may apply, you must see that the
                following are done:
                a. Give prompt notice to us or our agent;
                b. Notify the police in case of loss by theft;
                c. Notify the credit card or electronic fund transfer card company in case
                   of loss under Credit Card, Electronic Fund Transfer Card or Forgery and
                   Counterfeit Money coverage;
                d. Protect the property from further damage, make reasonable and necessary
                   repairs to protect the property, and keep an accurate record of repair
                   expenses;
                e. Cooperate with us in the investigation of a claim;
                f. Prepare an inventory of damaged personal property showing the quantity,
                   description, actual cash value and amount of loss;
                g. As often as we reasonably require, permit us to inspect the property,
                   examine your books and records, and submit to examination under oath;
                h. Submit to us, within 60 days after our request, your signed, sworn proof
                   of loss which sets forth the knowledge and belief of the insured as to
                   the time and cause of loss, interest of the insured and all others in
                   the property, all encumbrances on the property, and other insurance covering
                   the loss.

                Loss Settlement
                Covered property losses are settled as follows:
                a. Property of the following types: (1) Personal property; (2) Awnings,
                   carpeting, household appliances, outdoor antennas and outdoor equipment,
                   whether or not attached to buildings; at actual cash value at the time
                   of loss but not more than the amount required to repair or replace.
                b. Buildings covered under Coverage A or B at replacement cost without
                   deduction for depreciation, subject to certain conditions.
                """
            }
        ]
    },
    {
        "filename": "water_damage_exclusion_endorsement.pdf",
        "form_number": "WD-EXCL-01",
        "doc_type": "endorsement",
        "state": "CA",
        "effective_date": "2024-01-01",
        "title": "Water Damage Exclusion Endorsement",
        "content": [
            {
                "heading": "WATER DAMAGE EXCLUSION ENDORSEMENT",
                "text": """
                Form Number: WD-EXCL-01
                This endorsement modifies insurance provided under the following:
                HOMEOWNERS INSURANCE POLICY - FORM HO-3

                Policy Number: CA-HO-2024-001234
                Named Insured: John Doe
                Effective Date: January 1, 2024
                State: California
                """
            },
            {
                "heading": "SCHEDULE",
                "text": """
                The following Water Damage exclusions apply to this policy:

                1. Flood Damage Exclusion
                2. Sewer Backup Exclusion (can be added back with optional coverage)
                3. Surface Water Exclusion
                """
            },
            {
                "heading": "WATER DAMAGE EXCLUSION",
                "text": """
                This endorsement amends Section I - Exclusions.

                The Water Damage exclusion is replaced by the following:

                Water Damage means:
                a. Flood, surface water, waves, tidal water, overflow of a body of water,
                   or spray from any of these, whether or not driven by wind;
                b. Water or sewage from outside the residence premises plumbing system that
                   enters through sewers or drains, or water which enters into and overflows
                   from within a sump, sump pump or related equipment;
                c. Water below the surface of the ground, including water which exerts pressure
                   on or seeps or leaks through a building, sidewalk, driveway, foundation,
                   swimming pool or other structure.

                Direct loss by fire, explosion or theft resulting from water damage is covered.

                EXCEPTIONS TO WATER DAMAGE EXCLUSION

                We do cover:
                1. Water or steam from a household appliance, heating, air conditioning or
                   automatic fire protective sprinkler system or from a household appliance;
                2. Rain, snow, sleet or hail which enters through an opening in a roof or
                   wall made by the direct force of wind or hail;
                3. Sudden and accidental discharge or overflow of water or steam from within
                   a plumbing, heating, air conditioning or automatic fire protective sprinkler
                   system or from a household appliance.

                IMPORTANT NOTICE TO CALIFORNIA POLICYHOLDERS

                This exclusion eliminates coverage for certain water damage losses. You may
                wish to purchase separate flood insurance through the National Flood Insurance
                Program (NFIP) if your property is in a flood-prone area. Contact your agent
                for more information about flood insurance availability and requirements.

                Sewer backup coverage may be added to your policy for an additional premium.
                Contact your agent or insurance company to add this optional coverage.
                """
            },
            {
                "heading": "DEFINITIONS",
                "text": """
                The following definitions apply to this endorsement:

                "Flood" means a general and temporary condition of partial or complete inundation
                of two or more acres of normally dry land area or of two or more properties from:
                a. Overflow of inland or tidal waters;
                b. Unusual and rapid accumulation or runoff of surface waters from any source;
                c. Mudflow.

                "Surface Water" means water on the surface of the ground, whether or not flowing,
                and whether or not the water is moving toward, into, or in a river, stream, or
                other watercourse, and whether or not the water reaches or enters the watercourse.

                "Sewer Backup" means water or sewage from outside the residence premises plumbing
                system that backs up through sewers or drains into the residence premises.
                """
            },
            {
                "heading": "CLAIMS PROCEDURE",
                "text": """
                If you believe you have a covered water damage claim:

                1. Take immediate action to prevent further damage
                2. Document the damage with photographs
                3. Contact your insurance agent or company within 24 hours
                4. Keep receipts for emergency repairs
                5. Do not make permanent repairs until an adjuster has inspected the damage

                For water damage claims that may be excluded under this endorsement, we will
                investigate to determine coverage. If you disagree with our coverage decision,
                you have the right to appeal through the California Department of Insurance.
                """
            }
        ]
    },
    {
        "filename": "earthquake_coverage_info.pdf",
        "form_number": "EQ-INFO-CA",
        "doc_type": "disclosure",
        "state": "CA",
        "effective_date": "2024-01-01",
        "title": "Earthquake Insurance Disclosure - California",
        "content": [
            {
                "heading": "EARTHQUAKE INSURANCE DISCLOSURE",
                "text": """
                Form Number: EQ-INFO-CA
                State: California
                Disclosure Date: January 1, 2024

                IMPORTANT NOTICE REGARDING EARTHQUAKE COVERAGE

                California law requires that we offer you earthquake insurance coverage on your
                homeowners policy. This disclosure provides information about earthquake insurance
                and your options for coverage.
                """
            },
            {
                "heading": "WHAT IS EARTHQUAKE INSURANCE?",
                "text": """
                Earthquake insurance is a separate coverage that protects your home and personal
                property from damage caused by earthquakes and related perils such as:

                - Ground shaking
                - Surface rupture
                - Landslide or mudflow resulting from earthquake
                - Fire following earthquake (may be covered under standard homeowners policy)
                - Tsunami or seiche following earthquake

                Standard homeowners insurance policies exclude earthquake damage. To be protected
                against earthquake losses, you must purchase separate earthquake coverage.
                """
            },
            {
                "heading": "WHY CALIFORNIA REQUIRES THIS DISCLOSURE",
                "text": """
                California is located in an earthquake-prone region. Major earthquakes can cause
                catastrophic damage to homes and personal property. The California Earthquake
                Authority (CEA) and private insurers offer earthquake insurance to help
                homeowners protect their investment.

                According to the California Department of Insurance:
                - California has a 99.7% chance of experiencing a magnitude 6.7 or larger
                  earthquake in the next 30 years
                - The average cost to repair earthquake damage to a home is $50,000 to $150,000
                - Only 10-13% of California homeowners have earthquake insurance
                """
            },
            {
                "heading": "YOUR EARTHQUAKE INSURANCE OPTIONS",
                "text": """
                Option 1: California Earthquake Authority (CEA) Coverage
                The CEA is a publicly managed, privately funded organization that provides
                earthquake insurance to California homeowners. CEA policies offer:

                - Coverage for dwelling, personal property, and additional living expenses
                - Deductibles: 5%, 10%, 15%, 20%, or 25% of Coverage A (dwelling amount)
                - Lower premiums than many private market options
                - Backed by a combination of premium revenue, reinsurance, and financial reserves

                Option 2: Private Market Earthquake Coverage
                Some insurance companies offer earthquake coverage through the private market.
                These policies may offer:

                - Lower deductibles (some as low as 2.5%)
                - Higher coverage limits
                - More flexible policy terms
                - Potentially higher premiums

                Option 3: Decline Earthquake Coverage
                You may choose to decline earthquake coverage. If you decline, you will not
                have insurance protection for earthquake damage to your home or personal property.
                You would be responsible for all repair costs if your home is damaged in an
                earthquake.
                """
            },
            {
                "heading": "EARTHQUAKE INSURANCE COSTS",
                "text": """
                The cost of earthquake insurance varies based on several factors:

                1. Location - Homes closer to fault lines typically have higher premiums
                2. Construction Type - Wood frame homes usually cost less to insure than
                   unreinforced masonry homes
                3. Age of Home - Older homes may have higher premiums
                4. Foundation Type - Homes with bolted foundations may qualify for discounts
                5. Deductible Amount - Higher deductibles result in lower premiums
                6. Coverage Amount - Based on your dwelling coverage (Coverage A)

                Sample Annual Premium Estimates (Coverage A: $500,000):
                - 5% Deductible: $1,200 - $2,000
                - 10% Deductible: $800 - $1,200
                - 15% Deductible: $600 - $900
                - 20% Deductible: $500 - $700

                Note: These are estimates only. Actual premiums vary by location and other factors.
                """
            },
            {
                "heading": "IMPORTANT CONSIDERATIONS",
                "text": """
                Before deciding on earthquake coverage, consider:

                1. Your Financial Ability to Rebuild
                   Can you afford to repair or rebuild your home without insurance if a major
                   earthquake occurs? Consider your savings, emergency fund, and other assets.

                2. Your Mortgage Requirement
                   Some mortgage lenders may require earthquake insurance, especially for homes
                   in high-risk areas. Check with your lender.

                3. Deductible Amount
                   Earthquake deductibles are percentage-based, not flat amounts. A 10% deductible
                   on a $500,000 home means you pay the first $50,000 of damage. Choose a
                   deductible you can afford.

                4. Coverage Limitations
                   Review what is and isn't covered under earthquake policies. Some items may
                   have sub-limits or exclusions.

                5. Waiting Period
                   Most earthquake policies have a 10-30 day waiting period before coverage begins.
                   You cannot purchase coverage after an earthquake has occurred.
                """
            },
            {
                "heading": "HOW TO OBTAIN EARTHQUAKE COVERAGE",
                "text": """
                To add earthquake coverage to your homeowners policy:

                1. Contact your insurance agent or company
                2. Request a quote for CEA or private market earthquake coverage
                3. Review the coverage details, deductibles, and premium
                4. Complete and sign the earthquake insurance application
                5. Pay the additional premium

                If you decline earthquake coverage, you must complete and sign a written waiver
                stating that you understand the risks and choose not to purchase coverage.

                For more information:
                - California Earthquake Authority: www.earthquakeauthority.com or 1-877-797-4300
                - California Department of Insurance: www.insurance.ca.gov or 1-800-927-4357
                """
            },
            {
                "heading": "POLICYHOLDER ACKNOWLEDGMENT",
                "text": """
                I acknowledge that I have been offered earthquake insurance coverage and have
                received this disclosure document. I understand that:

                - Standard homeowners insurance does not cover earthquake damage
                - Earthquake insurance is available through the California Earthquake Authority
                  or private insurance companies
                - I have the option to purchase or decline earthquake coverage
                - If I decline coverage, I will not have insurance protection for earthquake
                  damage to my home or personal property

                By signing below, I indicate my choice regarding earthquake insurance:

                [ ] I wish to purchase CEA earthquake coverage
                [ ] I wish to purchase private market earthquake coverage
                [ ] I decline earthquake coverage at this time

                _________________           _____________________           _____________
                Policyholder Name           Policyholder Signature          Date
                """
            }
        ]
    }
]


def generate_pdf(doc_info, output_dir="pdfs"):
    """Generate a PDF document with the given content"""

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Full output path
    output_path = os.path.join(output_dir, doc_info["filename"])

    # Create PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch
    )

    # Container for flowables
    story = []

    # Styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor='#000000',
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='#000000',
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor='#000000',
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        leading=14
    )

    # Add title
    title = Paragraph(doc_info["title"], title_style)
    story.append(title)
    story.append(Spacer(1, 0.2*inch))

    # Add metadata
    metadata_text = f"""
    <b>Form Number:</b> {doc_info["form_number"]}<br/>
    <b>Document Type:</b> {doc_info["doc_type"].capitalize()}<br/>
    <b>State:</b> {doc_info["state"]}<br/>
    <b>Effective Date:</b> {doc_info["effective_date"]}<br/>
    <b>Generated:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    """
    metadata = Paragraph(metadata_text, body_style)
    story.append(metadata)
    story.append(Spacer(1, 0.3*inch))

    # Add content sections
    for section in doc_info["content"]:
        # Add heading
        heading = Paragraph(section["heading"], heading_style)
        story.append(heading)

        # Add text
        # Clean up the text (remove extra whitespace)
        text = ' '.join(section["text"].split())
        body = Paragraph(text, body_style)
        story.append(body)
        story.append(Spacer(1, 0.1*inch))

    # Build PDF
    doc.build(story)

    print(f"Generated: {output_path}")
    return output_path


def main():
    """Generate all sample PDFs"""
    print("Generating sample insurance PDFs...")
    print("=" * 60)

    generated_files = []

    for doc_info in SAMPLE_DOCUMENTS:
        try:
            output_path = generate_pdf(doc_info)
            generated_files.append(output_path)
        except Exception as e:
            print(f"Error generating {doc_info['filename']}: {e}")

    print("=" * 60)
    print(f"\nSuccessfully generated {len(generated_files)} PDF files:")
    for file_path in generated_files:
        print(f"  - {file_path}")

    print("\nThese PDFs can now be uploaded to RAGMesh for testing.")
    print("Use the Documents tab in the frontend to upload and index them.")


if __name__ == "__main__":
    main()
