///////////////////////////////////////////////////////////////////////////////
///                                                                         ///
///  HF MC generator for Pb-Pb                                              ///
///  Option 2: generate a background event with Angantyr                    ///
///            and inject N PYTHIA events triggered on ccbar and/or bbbar   ///
///                                                                         ///
///////////////////////////////////////////////////////////////////////////////

#include "generator_pythia8_gaptriggered_hf.C"

using namespace Pythia8;

namespace hf_generators
{
    enum GenType : int {
        GapTriggeredCharm = 0,      // --> GeneratorPythia8GapTriggeredCharm: charm enriched
        GapTriggeredBeauty,         // --> GeneratorPythia8GapTriggeredBeauty: beauty enriched
        GapTriggeredCharmAndBeauty, // --> GeneratorPythia8GapTriggeredCharmAndBeauty: charm and beauty enriched (with same ratio)
        GapHF,                      // --> GeneratorPythia8GapHF
        NGenType
    };
}

class GeneratorPythia8ManualEmbedHF : public o2::eventgen::GeneratorPythia8
{
public:

    /// default constructor
    GeneratorPythia8ManualEmbedHF() = default;

    ///  Destructor
    ~GeneratorPythia8ManualEmbedHF() = default;

    /// Init
    bool Init() override
    {
        return o2::eventgen::GeneratorPythia8::Init();
    }

    /// @brief setup the event generator for HF signals
    /// \param gentype generator type (only ccbar, only bbbar, both)
    /// \param yQuarkMin minimum quark rapidity
    /// \param yQuarkMax maximum quark rapidity
    /// \param yHadronMin minimum hadron rapidity
    /// \param yHadronMax maximum hadron rapidity
    /// \param hadronPdgList list of PDG codes for hadrons to be used in trigger
    void setupGeneratorEvHF(int genType, float yQuarkMin, float yQuarkMax, float yHadronMin, float yHadronMax, std::vector<int> hadronPdgList = {}) {
        mGeneratorEvHF = nullptr;
        switch (genType)
        {
        case hf_generators::GapTriggeredCharm:
            LOG(info) << "********** [GeneratorPythia8ManualEmbedHF] configuring GeneratorPythia8GapTriggeredCharm **********";
            LOG(info) << "**********                                 number of HF signal events to be merged: " << mNumSigEvs;
            mGeneratorEvHF = dynamic_cast<GeneratorPythia8GapTriggeredHF*>(GeneratorPythia8GapTriggeredCharm(/*no gap trigger*/1, yQuarkMin, yQuarkMax, yHadronMin, yHadronMax, hadronPdgList));
            break;
        case hf_generators::GapTriggeredBeauty:
            LOG(info) << "********** [GeneratorPythia8ManualEmbedHF] configuring GeneratorPythia8GapTriggeredBeauty **********";
            LOG(info) << "**********                                 number of HF signal events to be merged: " << mNumSigEvs;
            mGeneratorEvHF = dynamic_cast<GeneratorPythia8GapTriggeredHF*>(GeneratorPythia8GapTriggeredBeauty(/*no gap trigger*/1, yQuarkMin, yQuarkMax, yHadronMin, yHadronMax, hadronPdgList));
            break;
        case hf_generators::GapTriggeredCharmAndBeauty:
            LOG(info) << "********** [GeneratorPythia8ManualEmbedHF] configuring GeneratorPythia8GapTriggeredCharmAndBeauty **********";
            LOG(info) << "**********                                 number of HF signal events to be merged: " << mNumSigEvs;
            mGeneratorEvHF = dynamic_cast<GeneratorPythia8GapTriggeredHF*>(GeneratorPythia8GapTriggeredCharmAndBeauty(/*no gap trigger*/1, yQuarkMin, yQuarkMax, yHadronMin, yHadronMax, hadronPdgList));
            break;
        case hf_generators::GapHF:
            LOG(info) << "********** [GeneratorPythia8ManualEmbedHF] configuring GeneratorPythia8GapHF **********";
            LOG(info) << "**********                                 number of HF signal events to be merged: " << mNumSigEvs;
            mGeneratorEvHF = dynamic_cast<GeneratorPythia8GapTriggeredHF*>(GeneratorPythia8GapHF(/*no gap trigger*/1, yQuarkMin, yQuarkMax, yHadronMin, yHadronMax, hadronPdgList));
            break;
        default:
            LOG(fatal) << "********** [GeneratorPythia8ManualEmbedHF] bad configuration, fix it! **********";
            break;
        }
        mGeneratorEvHF->Init();
    }

    /// @brief configure the generator settings for underlying event simulation
    void configureGeneratorUE() {

        ///______________________________________________
        ///______________________________________________
        ///______________________________________________

        /////////////////////////////////////////////////
        ///                                           ///
        ///  MC for Pb-Pb - underlying event          ///
        ///  Write here the PYTHIA Angantyr settings  ///
        ///                                           ///
        /////////////////////////////////////////////////

        /// beams
        this->readString("Beams:idA = 1000822080"); // Pb
        this->readString("Beams:idB = 1000822080"); // Pb
        this->readString("Beams:eCM = 5360.000000"); // centre-of-mass energy (GeV)

        /// heavy-ion settings (valid for Pb-Pb 5520 only) 
        this->readString("HeavyIon:SigFitNGen = 0");
        this->readString("HeavyIon:SigFitDefPar = 13.88,1.84,0.22,0.0,0.0,0.0,0.0,0.0");
        this->readString("HeavyIon:bWidth = 14.48");

        ///______________________________________________
        ///______________________________________________
        ///______________________________________________
    }

    /// @brief configure the generator settings for HF events simulation
    void configureGeneratorHF() {

        ///______________________________________________
        ///______________________________________________
        ///______________________________________________

        /////////////////////////////////////////////////
        ///                                           ///
        ///  MC for Pb-Pb - HF signal events          ///
        ///  Write here the Mode 2 settings           ///
        ///  and hardQCD settings                     ///
        ///                                           ///
        /////////////////////////////////////////////////

        /// beams
        mGeneratorEvHF->readString("Beams:idA = 2212"); // pp
        mGeneratorEvHF->readString("Beams:idB = 2212"); // pp
        mGeneratorEvHF->readString("Beams:eCM = 5360.000000"); // centre-of-mass energy

        /// processes: c-cbar and b-bbar processes
        mGeneratorEvHF->readString("HardQCD:hardccbar on");
        mGeneratorEvHF->readString("HardQCD:hardbbbar on");
        mGeneratorEvHF->readString("HardQCD:gg2ccbar on");
        mGeneratorEvHF->readString("HardQCD:qqbar2ccbar on");
        mGeneratorEvHF->readString("HardQCD:gg2bbbar on");
        mGeneratorEvHF->readString("HardQCD:qqbar2bbbar on");

        /// Pythia Mode 2
        mGeneratorEvHF->readString("ColourReconnection:mode 1");
        mGeneratorEvHF->readString("ColourReconnection:allowDoubleJunRem off");
        mGeneratorEvHF->readString("ColourReconnection:m0 0.3");
        mGeneratorEvHF->readString("ColourReconnection:allowJunctions on");
        mGeneratorEvHF->readString("ColourReconnection:junctionCorrection 1.20");
        mGeneratorEvHF->readString("ColourReconnection:timeDilationMode 2");
        mGeneratorEvHF->readString("ColourReconnection:timeDilationPar 0.18");
        mGeneratorEvHF->readString("StringPT:sigma 0.335");
        mGeneratorEvHF->readString("StringZ:aLund 0.36");
        mGeneratorEvHF->readString("StringZ:bLund 0.56");
        mGeneratorEvHF->readString("StringFlav:probQQtoQ 0.078");
        mGeneratorEvHF->readString("StringFlav:ProbStoUD 0.2");
        mGeneratorEvHF->readString("StringFlav:probQQ1toQQ0join 0.0275,0.0275,0.0275,0.0275");
        mGeneratorEvHF->readString("MultiPartonInteractions:pT0Ref 2.15");
        mGeneratorEvHF->readString("BeamRemnants:remnantMode 1");
        mGeneratorEvHF->readString("BeamRemnants:saturation 5");

        ///______________________________________________
        ///______________________________________________
        ///______________________________________________
    }

protected:

    /// @brief This function actually generated only the underlying event
    Bool_t generateEvent() override
    {

        /// generate the underlying event with this generator
        bool genOk = false;
        while(!genOk) {
            genOk = mPythia.next();
        }
        
        /// determine the impact parameter and consequently the number of signal events
        mCollisionImpPar = mPythia.info.hiInfo.b();
        float x = mCollisionImpPar;
        mNumSigEvs = std::max(1.,120.*(x<5.)+80.*(1.-x/20.)*(x>5.)*(x<11.)+240.*(1.-x/13.)*(x>11.));
        LOG(info) << "-----> generating " << mNumSigEvs << " signal events " << std::endl;

        return true;
    }

    Bool_t importParticles() override
    {
        /// Import particles from generated underlying event
        this->importParticles();

        /// Generate mNumSigEvs HF events to be merged in one
        int nEvsHF = 0;
        while(nEvsHF < mNumSigEvs) {
        
            /// generate the HF event
            bool genOk = false;
            while(!genOk) {
                genOk = (mGeneratorEvHF->generateEvent() && mGeneratorEvHF->importParticles() /*copy particles from mGeneratorEvHF.mPythia.event to mGeneratorEvHF.mParticles*/ );
            }
        
            /// copy the particles from the HF event in the particle stack
            auto particlesHfEvent = mGeneratorEvHF->getParticles();
            int originalSize = mParticles.size(); // stack of this event generator
            for(int iPart=0; iPart<particlesHfEvent.size(); iPart++) {
              auto particle = particlesHfEvent.at(iPart);
        
              /// adjust the particle mother and daughter indices
              if(particle.GetFirstMother() >= 0)   particle.SetFirstMother(particle.GetFirstMother() + originalSize);
        	    if(particle.GetFirstDaughter() >= 0) particle.SetFirstDaughter(particle.GetFirstDaughter() + originalSize);
        	    if(particle.GetLastDaughter() >= 0)  particle.SetLastDaughter(particle.GetLastDaughter() + originalSize);
        
              /// copy inside this.mParticles from mGeneratorEvHF.mParticles, i.e. the particles generated in mGeneratorEvHF
              mParticles.push_back(particle);
            }
        
            /// one more event generated, let's update the counter and clear it, to allow the next generation
            nEvsHF++;
            //mGeneratedEvents++;
            mGeneratorEvHF->clearParticles();
        }
    }

private:

    GeneratorPythia8* mGeneratorEvHF; // to generate HF signal events
    
    int mNumSigEvs; // number of HF signal events to be merged in one Pythia event
    float mCollisionImpPar; // impacta parameter between the two nuclei in the underlying event

};


// Charm and beauty enriched (with same ratio)
FairGenerator * GeneratorPythia8ManualEmbedHFCharmAndBeauty(float yQuarkMin = -1.5, float yQuarkMax = 1.5, float yHadronMin = -1.5, float yHadronMax = 1.5, std::vector<int> hadronPdgList = {})
{
    auto myGen = new GeneratorPythia8ManualEmbedHF();
    auto seed = (gRandom->TRandom::GetSeed() % 900000000);
    myGen->readString("Random:setSeed on");
    myGen->readString("Random:seed " + std::to_string(seed));

    /// configure the generator for the underlying event
    ///
    ///   NB: the .cfg file must not contain infos about the collision-system and tune settings
    ///
    myGen->configureGeneratorUE();

    /// setup the internal generator for HF events
    ///
    ///   NB: the .cfg file must not contain infos about the collision-system and tune settings
    ///
    myGen->setupGeneratorEvHF(hf_generators::GapTriggeredCharmAndBeauty, yQuarkMin, yQuarkMax, yHadronMin, yHadronMax, hadronPdgList);
    myGen->configureGeneratorHF();


    return myGen;
}