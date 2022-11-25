********************************
* SAMPLE PROGRAM 1 *
********************************
*
         ORG $F000
*
START    SEI
         CLD
         LDX #$FF
         TXS
         LDA #$00
*
ZERO     STA $00,X
         DEX
         BNE ZERO
         END
